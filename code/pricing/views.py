import datetime
import threading
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
_EMBEDDING_MODEL_LOCK = threading.Lock()


def get_embedding_model():
    """Load the embedding model once per process, lazily, never per request."""
    global _EMBEDDING_MODEL
    if _EMBEDDING_MODEL is None:
        with _EMBEDDING_MODEL_LOCK:
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
    db_items_count: int = 0
    qdrant_error: bool = False
    empty_index: bool = False


def get_corpus_info(
    client: Any = None,
    model: Any = None,
    reference_date: datetime.date | None = None,
) -> CorpusInfo:
    """Return corpus index metadata read from DB and Qdrant."""
    from django.core.cache import cache
    from django.db.models import Max, Min
    from qdrant_client import models as qmodels

    from ingestion.models import PublicItem

    window_start, window_end = get_screening_date_window(reference_date)

    # Cache PostgreSQL count for 5 minutes to avoid COUNT(*) on every request (N1)
    db_count = cache.get("corpus_db_items_count")
    if db_count is None:
        db_count = PublicItem.objects.count()
        cache.set("corpus_db_items_count", db_count, 300)

    indexed_count = 0
    qdrant_error = False
    empty_index = False
    start_date = None
    end_date = None

    try:
        if client is None:
            from semantic_index import get_qdrant_client

            client = get_qdrant_client()
        if model is None:
            model = get_embedding_model()
        from semantic_index.embedding import collection_name_for_model

        coll_name = collection_name_for_model(model)
        if not client.collection_exists(coll_name):
            empty_index = True
        else:
            count_res = client.count(collection_name=coll_name)
            indexed_count = getattr(count_res, "count", 0)
            if indexed_count == 0:
                empty_index = True
            else:
                # Read earliest and latest published_on from Qdrant indexed payloads (N1)
                try:
                    asc_points, _ = client.scroll(
                        collection_name=coll_name,
                        limit=1,
                        with_payload=["published_on"],
                        order_by=qmodels.OrderBy(
                            key="published_on", direction=qmodels.Direction.ASC
                        ),
                    )
                    desc_points, _ = client.scroll(
                        collection_name=coll_name,
                        limit=1,
                        with_payload=["published_on"],
                        order_by=qmodels.OrderBy(
                            key="published_on", direction=qmodels.Direction.DESC
                        ),
                    )
                    if asc_points and asc_points[0].payload:
                        raw_start = asc_points[0].payload.get("published_on")
                        if raw_start:
                            start_date = datetime.date.fromisoformat(str(raw_start))
                    if desc_points and desc_points[0].payload:
                        raw_end = desc_points[0].payload.get("published_on")
                        if raw_end:
                            end_date = datetime.date.fromisoformat(str(raw_end))
                except Exception:
                    start_date = None
                    end_date = None
    except Exception:
        qdrant_error = True
        indexed_count = 0

    # Fallback to DB date bounds if Qdrant didn't provide dates (e.g. mocked client without scroll)
    if start_date is None or end_date is None:
        bounds = PublicItem.objects.aggregate(
            min_date=Min("published_on"), max_date=Max("published_on")
        )
        if start_date is None:
            start_date = bounds.get("min_date")
        if end_date is None:
            end_date = bounds.get("max_date")
    if qdrant_error or empty_index or indexed_count == 0 or start_date is None or end_date is None:
        is_partial = True
    else:
        # Tolerate 1 day of lag at end_date (e.g. yesterday) (N1)
        tolerated_end = window_end - datetime.timedelta(days=1)
        if start_date > window_start or end_date < tolerated_end or indexed_count < db_count:
            is_partial = True
        else:
            is_partial = False

    return CorpusInfo(
        indexed_items_count=indexed_count,
        start_date=start_date,
        end_date=end_date,
        is_partial=is_partial,
        db_items_count=db_count,
        qdrant_error=qdrant_error,
        empty_index=empty_index,
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
    try:
        raw_results = fn(query=item.description, date_window=date_window, limit=limit)
    except Exception:
        return []

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
    candidates: list[Any] | None = None,
) -> dict:
    if item is None:
        return EstimatePanel(EMPTY_PANEL, counted_candidate_ids=set())

    if candidates is None:
        candidates = get_screening_candidates(item)

    counted_candidate_ids: set[int] = set()
    for c in candidates:
        from ingestion.units import normalize_unit

        if decisions.get(c.id) == "accept" and normalize_unit(c.unit) == normalize_unit(item.unit):
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

    item_id_raw = request.POST.get("item_id")
    item_id = int(item_id_raw) if item_id_raw else getattr(candidate, "item_id", None)
    item = get_item(item_id) if item_id else None
    item_unit = item.unit if item else None

    decisions = request.session.get("screening_decisions", {})
    dec_key = f"{item_id}:{candidate_id}" if item_id else str(candidate_id)
    decisions[dec_key] = decision
    request.session["screening_decisions"] = decisions

    expected_price = parse_expected_price(request.POST.get("expected_price"))
    cand_price = getattr(candidate, "price", None)
    prox = (
        compute_proximity(cand_price, expected_price, candidate.unit, item_unit)
        if cand_price is not None
        else None
    )
    proximity = format_proximity(cand_price, expected_price, prox, candidate.unit, item_unit)

    item_decisions = {}
    for k, v in decisions.items():
        if ":" in str(k):
            it_str, cand_str = str(k).split(":", 1)
            if item_id is None or int(it_str) == item_id:
                item_decisions[int(cand_str)] = v
        elif item_id is None:
            item_decisions[int(k)] = v

    estimate = build_estimate_panel(item, item_decisions)

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

    raw_decisions = request.session.get("screening_decisions", {})
    decisions = {}
    for k, v in raw_decisions.items():
        if ":" in str(k):
            it_str, cand_str = str(k).split(":", 1)
            if int(it_str) == item_id:
                decisions[int(cand_str)] = v
        elif not any(":" in str(other_k) for other_k in raw_decisions):
            # Backward compatibility with un-scoped decisions
            decisions[int(k)] = v
    estimate = build_estimate_panel(item, decisions, candidates=candidates)

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
