import datetime
from collections.abc import Sequence  # noqa: F401
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.http import require_POST

from procurement.demo_data import get_item, get_procurement_for_item

from . import demo_data
from .candidates import candidate_from_public_item, fetch_awarded_price_on_demand
from .estimation import (
    calculate_mean,
    calculate_median,
    calculate_min,
    get_calculation_prices,
    requires_justification,
)
from .ranking import compute_proximity, format_proximity, parse_expected_price, rank_candidates

DEFAULT_MODEL = "intfloat/multilingual-e5-base"
DEFAULT_REVISION = "d13f1b27baf31030b7fd040960d60d909913633f"

_EMBEDDING_MODEL: Any = None


def get_embedding_model():
    """Load the embedding model once per process, lazily, never per request."""
    global _EMBEDDING_MODEL
    if _EMBEDDING_MODEL is None:
        from semantic_index.embedding import SentenceTransformerEmbeddingModel

        _EMBEDDING_MODEL = SentenceTransformerEmbeddingModel(
            model_name=DEFAULT_MODEL,
            revision=DEFAULT_REVISION,
        )
    return _EMBEDDING_MODEL


def get_screening_date_window(
    reference_date: datetime.date | None = None,
) -> tuple[datetime.date, datetime.date]:
    """Return the mandatory 12-month date window up to reference_date (RN07)."""
    end_date = reference_date or datetime.date.today()
    try:
        start_date = end_date.replace(year=end_date.year - 1)
    except ValueError:
        start_date = end_date - datetime.timedelta(days=365)
    return (start_date, end_date)


def default_search_function(
    query: str,
    date_window: tuple[datetime.date, datetime.date],
    limit: int = 20,
):
    """Execute semantic search against Qdrant and PostgreSQL under structured date window."""
    from semantic_index.search import StructuredFilter, semantic_search

    model = get_embedding_model()
    structured_filter = StructuredFilter(date_window=date_window)
    return semantic_search(
        model=model,
        query=query,
        structured_filter=structured_filter,
        limit=limit,
    )


search_function = default_search_function


@dataclass(frozen=True)
class CorpusInfo:
    """Metadata about the semantic index corpus and its date coverage."""

    indexed_items_count: int
    start_date: datetime.date | None
    end_date: datetime.date | None
    is_partial: bool


def get_corpus_info(
    client: Any = None,
    model: Any = None,
    reference_date: datetime.date | None = None,
) -> CorpusInfo:
    """Return corpus index metadata read from DB and Qdrant."""
    from django.db.models import Max, Min

    from ingestion.models import PublicItem

    window_start, window_end = get_screening_date_window(reference_date)

    bounds = PublicItem.objects.aggregate(
        min_date=Min("published_on"), max_date=Max("published_on")
    )
    start_date = bounds.get("min_date")
    end_date = bounds.get("max_date")
    db_count = PublicItem.objects.count()

    indexed_count = 0
    try:
        if client is None:
            from semantic_index import get_qdrant_client

            client = get_qdrant_client()
        if model is None:
            model = get_embedding_model()
        from semantic_index.embedding import collection_name_for_model

        coll_name = collection_name_for_model(model)
        if client.collection_exists(coll_name):
            count_res = client.count(collection_name=coll_name)
            indexed_count = getattr(count_res, "count", 0)
    except Exception:
        indexed_count = 0

    if indexed_count == 0 or start_date is None or end_date is None:
        is_partial = False
    elif start_date > window_start or end_date < window_end or indexed_count < db_count:
        is_partial = True
    else:
        is_partial = False

    return CorpusInfo(
        indexed_items_count=indexed_count,
        start_date=start_date,
        end_date=end_date,
        is_partial=is_partial,
    )


corpus_info_function = get_corpus_info


def get_screening_candidates(
    item,
    expected_price: Decimal | None = None,
    search_fn: Any = None,
    limit: int = 20,
) -> list[Any]:
    """Fetch and rank screening candidates for an item from semantic search."""
    fn = search_fn or search_function
    date_window = get_screening_date_window()
    raw_results = fn(query=item.description, date_window=date_window, limit=limit)

    candidates: list[Any] = []
    for res in raw_results:
        if hasattr(res, "item") and hasattr(res, "score"):
            public_item = res.item
            score = res.score
            fetch_awarded_price_on_demand(public_item)
            candidate = candidate_from_public_item(public_item, similarity=score, item_id=item.id)
            candidates.append(candidate)
        elif isinstance(res, tuple) and len(res) == 2:
            public_item, score = res
            fetch_awarded_price_on_demand(public_item)
            candidate = candidate_from_public_item(public_item, similarity=score, item_id=item.id)
            candidates.append(candidate)
        else:
            candidates.append(res)

    return rank_candidates(candidates, expected_price, item.unit)


class EstimatePanel(dict):
    """Estimate panel data dictionary preserving counted candidate IDs for template agreement."""

    def __init__(self, data: dict, counted_candidate_ids: set[int] | None = None):
        super().__init__(data)
        self.counted_candidate_ids = (
            counted_candidate_ids if counted_candidate_ids is not None else set()
        )

    def __getitem__(self, item):
        if item == "counted_candidate_ids":
            return self.counted_candidate_ids
        return super().__getitem__(item)

    def get(self, key, default=None):
        if key == "counted_candidate_ids":
            return self.counted_candidate_ids
        return super().get(key, default)

    def __contains__(self, key):
        if key == "counted_candidate_ids":
            return True
        return super().__contains__(key)


EMPTY_PANEL = {
    "mean": None,
    "median": None,
    "min": None,
    "count": 0,
    "requires_justification": False,
}


def build_estimate_panel(
    item,
    decisions: dict,
) -> dict:
    if item is None:
        return EstimatePanel(EMPTY_PANEL, counted_candidate_ids=set())

    candidates = get_screening_candidates(item)

    counted_candidate_ids: set[int] = set()
    for c in candidates:
        if decisions.get(c.id) == "accept" and c.unit == item.unit:
            if hasattr(c, "usable_calculation_price"):
                if c.usable_calculation_price is not None:
                    counted_candidate_ids.add(c.id)
            elif (
                not getattr(c, "is_estimated", False)
                and not getattr(c, "secret_budget", False)
                and getattr(c, "price", None) is not None
                and c.price > Decimal("0.00")
            ):
                counted_candidate_ids.add(c.id)

    counted_candidates = [c for c in candidates if c.id in counted_candidate_ids]
    prices = get_calculation_prices(counted_candidates)

    count = len(prices)
    if count == 0:
        return EstimatePanel(EMPTY_PANEL, counted_candidate_ids=set())

    return EstimatePanel(
        {
            "mean": calculate_mean(prices),
            "median": calculate_median(prices),
            "min": calculate_min(prices),
            "count": count,
            "requires_justification": requires_justification(prices),
        },
        counted_candidate_ids=counted_candidate_ids,
    )


@require_POST
def decide(request, candidate_id):
    from ingestion.models import PublicItem

    pi = PublicItem.objects.filter(pk=candidate_id).prefetch_related("raw_records").first()
    if pi is not None:
        fetch_awarded_price_on_demand(pi)
        candidate = candidate_from_public_item(pi)
    else:
        candidate = demo_data.get_candidate(candidate_id)

    if candidate is None:
        raise Http404("Candidate not found")

    decision = request.POST.get("decision")
    if decision not in ["accept", "reject"]:
        return HttpResponseBadRequest(b"Invalid decision")

    decisions = request.session.get("screening_decisions", {})
    decisions[str(candidate_id)] = decision
    request.session["screening_decisions"] = decisions

    item_id_raw = request.POST.get("item_id")
    item_id = int(item_id_raw) if item_id_raw else getattr(candidate, "item_id", None)
    item = get_item(item_id) if item_id else None
    item_unit = item.unit if item else None

    expected_price = parse_expected_price(request.POST.get("expected_price"))
    cand_price = getattr(candidate, "price", None)
    prox = (
        compute_proximity(cand_price, expected_price, candidate.unit, item_unit)
        if cand_price is not None
        else None
    )
    proximity = format_proximity(cand_price, expected_price, prox, candidate.unit, item_unit)

    adapted_decisions = {int(k): v for k, v in decisions.items()}
    estimate = build_estimate_panel(item, adapted_decisions)

    return render(
        request,
        "pricing/_candidate.html",
        {
            "candidate": candidate,
            "decision": decision,
            "proximity": proximity,
            "expected_price": expected_price,
            "item_unit": item_unit,
            "item_id": item.id if item else None,
            "estimate": estimate,
            "oob_estimate": estimate,
        },
    )


def screening(request, item_id):
    item = get_item(item_id)
    if item is None:
        raise Http404("Item not found")

    procurement = get_procurement_for_item(item_id)

    raw_expected_price = request.GET.get("expected_price")
    expected_price = parse_expected_price(raw_expected_price)
    expected_price_ignored = bool(
        raw_expected_price and raw_expected_price.strip() and expected_price is None
    )

    candidates = get_screening_candidates(
        item,
        expected_price=expected_price,
        search_fn=search_function,
        limit=20,
    )

    decisions = {int(k): v for k, v in request.session.get("screening_decisions", {}).items()}
    estimate = build_estimate_panel(item, decisions)

    proximities = {
        candidate.id: format_proximity(
            candidate.price,
            expected_price,
            compute_proximity(candidate.price, expected_price, candidate.unit, item.unit),
            candidate.unit,
            item.unit,
        )
        for candidate in candidates
    }

    corpus_info = corpus_info_function()

    return render(
        request,
        "pricing/screening.html",
        {
            "procurement": procurement,
            "item": item,
            "candidates": candidates,
            "decisions": decisions,
            "proximities": proximities,
            "expected_price": expected_price,
            "expected_price_ignored": expected_price_ignored,
            "estimate": estimate,
            "corpus_info": corpus_info,
        },
    )
