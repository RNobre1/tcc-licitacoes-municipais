import contextlib
import datetime
import threading
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from django.db import connections
from django.db.models import prefetch_related_objects
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.http import require_POST

from ingestion.units import normalize_unit
from procurement.demo_data import get_item, get_procurement_for_item

from . import demo_data
from .candidates import (
    Candidate,
    apply_fetched_item_result_record,
    candidate_from_public_item,
    fetch_awarded_price_on_demand,
    fetch_item_results_network,
    has_pending_result,
    is_fetch_failure_cached,
    record_fetch_failure,
)
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
MAX_SCREENING_CANDIDATES = 20
ON_DEMAND_FETCH_TIMEOUT_SECONDS = 2.0
PAGE_FETCH_BUDGET_SECONDS = 3.0

_EMBEDDING_MODEL: Any = None
_EMBEDDING_MODEL_LOCK = threading.Lock()
_ORIGINAL_FETCH_AWARDED_PRICE_ON_DEMAND = fetch_awarded_price_on_demand


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
    limit: int = MAX_SCREENING_CANDIDATES,
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
    model_error: bool = False


def get_corpus_info(
    client: Any = None,
    model: Any = None,
    reference_date: datetime.date | None = None,
) -> CorpusInfo:
    """Return corpus index metadata read from DB and Qdrant."""
    from django.core.cache import cache

    from ingestion.models import PublicItem

    window_start, window_end = get_screening_date_window(reference_date)

    # Cache PostgreSQL count for 5 minutes to avoid COUNT(*) on every request (N1)
    db_count = cache.get("corpus_db_items_count")
    if db_count is None:
        db_count = PublicItem.objects.count()
        cache.set("corpus_db_items_count", db_count, 300)

    indexed_count = 0
    qdrant_error = False
    model_error = False
    empty_index = False
    start_date = None
    end_date = None

    if model is None:
        if search_function is default_search_function:
            try:
                model = get_embedding_model()
            except Exception:
                model_error = True
        elif _EMBEDDING_MODEL is not None:
            model = _EMBEDDING_MODEL
        else:
            from collections import namedtuple

            _ModelMeta = namedtuple("_ModelMeta", ["name", "revision"])
            model = _ModelMeta(name=DEFAULT_MODEL, revision=DEFAULT_REVISION)

    if not model_error:
        try:
            from qdrant_client import models as qmodels

            if client is None:
                from semantic_index import get_qdrant_client

                client = get_qdrant_client()

            from semantic_index.embedding import collection_name_for_model

            coll_name = collection_name_for_model(model)
            index_cache_key = f"corpus_index_info:{coll_name}"
            cached_index_info = cache.get(index_cache_key)
            if cached_index_info is not None:
                indexed_count, start_date, end_date, empty_index = cached_index_info
            else:
                if not client.collection_exists(coll_name):
                    empty_index = True
                else:
                    count_res = client.count(collection_name=coll_name)
                    indexed_count = int(getattr(count_res, "count", 0) or 0)
                    empty_index = indexed_count == 0
                    if not empty_index:
                        # Read the covered range from Qdrant's indexed payloads.
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
                        if asc_points:
                            raw_start = (asc_points[0].payload or {}).get("published_on")
                            if raw_start:
                                start_date = datetime.date.fromisoformat(str(raw_start))
                        if desc_points:
                            raw_end = (desc_points[0].payload or {}).get("published_on")
                            if raw_end:
                                end_date = datetime.date.fromisoformat(str(raw_end))
                        if start_date is None or end_date is None:
                            start_date = None
                            end_date = None

                cache.set(
                    index_cache_key,
                    (indexed_count, start_date, end_date, empty_index),
                    300,
                )
        except Exception:
            qdrant_error = True
            indexed_count = 0
            start_date = None
            end_date = None
            empty_index = False

    if (
        model_error
        or qdrant_error
        or empty_index
        or indexed_count == 0
        or start_date is None
        or end_date is None
    ):
        is_partial = True
    else:
        # One day of lag is expected because a complete daily collection ends yesterday.
        tolerated_end = window_end - datetime.timedelta(days=1)
        if start_date > window_start or end_date < tolerated_end or indexed_count != db_count:
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
        model_error=model_error,
    )


corpus_info_function = get_corpus_info


def get_screening_candidates(
    item,
    expected_price: Decimal | None = None,
    search_fn: Any = None,
    limit: int = MAX_SCREENING_CANDIDATES,
) -> list[Any]:
    """Fetch and rank screening candidates for an item from semantic search."""
    from ingestion.models import PublicItem

    fn = search_fn or search_function
    date_window = get_screening_date_window()
    limit = max(0, min(limit, MAX_SCREENING_CANDIDATES))
    try:
        raw_results = list(fn(query=item.description, date_window=date_window, limit=limit) or [])[
            :limit
        ]
    except Exception:
        return []

    extracted = []
    for res in raw_results:
        if hasattr(res, "item") and hasattr(res, "score"):
            extracted.append((res.item, res.score))
        elif isinstance(res, tuple) and len(res) == 2:
            extracted.append((res[0], res[1]))
        else:
            extracted.append((res, None))

    db_items = [
        public_item
        for public_item, _ in extracted
        if isinstance(public_item, PublicItem) and not public_item._state.adding
    ]
    if db_items:
        prefetch_related_objects(db_items, "raw_records")

    using_default_fetch = fetch_awarded_price_on_demand is _ORIGINAL_FETCH_AWARDED_PRICE_ON_DEMAND
    if using_default_fetch:
        items_to_fetch = [
            public_item
            for public_item, _ in extracted
            if hasattr(public_item, "pk")
            and has_pending_result(public_item)
            and not is_fetch_failure_cached(public_item)
        ]
        if items_to_fetch:
            from concurrent.futures import ThreadPoolExecutor, wait

            def _fetch_network_only(public_item):
                try:
                    return fetch_item_results_network(
                        public_item, timeout=ON_DEMAND_FETCH_TIMEOUT_SECONDS
                    )
                finally:
                    connections.close_all()

            executor = ThreadPoolExecutor(max_workers=len(items_to_fetch))
            future_to_item = {
                executor.submit(_fetch_network_only, public_item): public_item
                for public_item in items_to_fetch
            }
            done, not_done = wait(future_to_item, timeout=PAGE_FETCH_BUDGET_SECONDS)
            executor.shutdown(wait=False, cancel_futures=True)

            for future in not_done:
                record_fetch_failure(future_to_item[future])

            for future in done:
                public_item = future_to_item[future]
                try:
                    record = future.result()
                except Exception:
                    record_fetch_failure(public_item)
                else:
                    with contextlib.suppress(Exception):
                        apply_fetched_item_result_record(public_item, record)
    else:
        items_to_fetch = [public_item for public_item, _ in extracted if hasattr(public_item, "pk")]
        if items_to_fetch:
            from concurrent.futures import ThreadPoolExecutor, wait

            def _run_custom_fetch(public_item):
                try:
                    return fetch_awarded_price_on_demand(
                        public_item, timeout=ON_DEMAND_FETCH_TIMEOUT_SECONDS
                    )
                finally:
                    connections.close_all()

            executor = ThreadPoolExecutor(max_workers=len(items_to_fetch))
            future_to_item = {
                executor.submit(_run_custom_fetch, public_item): public_item
                for public_item in items_to_fetch
            }
            _, not_done = wait(future_to_item, timeout=PAGE_FETCH_BUDGET_SECONDS)
            executor.shutdown(wait=False, cancel_futures=True)
            for future in not_done:
                record_fetch_failure(future_to_item[future])

    candidates: list[Any] = []
    for public_item, score in extracted:
        if score is not None:
            candidates.append(
                candidate_from_public_item(public_item, similarity=score, item_id=item.id)
            )
        else:
            candidates.append(public_item)

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
    candidates: list[Any],
) -> dict:
    if item is None:
        return EstimatePanel(EMPTY_PANEL, counted_candidate_ids=set())

    calculation_candidates = []
    for candidate in candidates:
        if isinstance(candidate, demo_data.PriceCandidate):
            candidate = Candidate(
                id=candidate.id,
                description=candidate.description,
                unit=candidate.unit,
                quantity=candidate.quantity,
                agency=candidate.agency,
                date=candidate.date,
                source=candidate.source,
                provenance=candidate.provenance,
                similarity=candidate.similarity,
                awarded_unit_price=candidate.price,
                item_id=candidate.item_id,
            )
        if not isinstance(candidate, Candidate):
            raise TypeError(f"Expected Candidate, got {type(candidate).__name__}")
        calculation_candidates.append(candidate)

    counted_candidate_ids: set[int] = set()
    for c in calculation_candidates:
        if (
            decisions.get(c.id) == "accept"
            and normalize_unit(c.unit) == normalize_unit(item.unit)
            and c.usable_calculation_price is not None
        ):
            counted_candidate_ids.add(c.id)

    counted_candidates = [c for c in calculation_candidates if c.id in counted_candidate_ids]
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


def _parse_item_decisions(raw_decisions: dict, item_id: int) -> dict[int, str]:
    item_decisions: dict[int, str] = {}
    for k, v in raw_decisions.items():
        if ":" in str(k):
            it_str, cand_str = str(k).split(":", 1)
            try:
                if int(it_str) == item_id:
                    item_decisions[int(cand_str)] = v
            except ValueError:
                continue
    return item_decisions


def build_item_estimate_panel(
    item,
    item_decisions: dict[int, str],
    current_candidates: list[Any] | None = None,
) -> tuple[dict, int]:
    """Build the estimate panel from all accepted candidates of an item."""
    from ingestion.models import PublicItem

    if item is None:
        return build_estimate_panel(None, item_decisions, candidates=[]), 0

    current_by_id = {c.id: c for c in (current_candidates or [])}
    accepted_ids = [
        accepted_id for accepted_id, value in item_decisions.items() if value == "accept"
    ]
    missing_ids = [accepted_id for accepted_id in accepted_ids if accepted_id not in current_by_id]
    public_items = PublicItem.objects.in_bulk(missing_ids) if missing_ids else {}

    panel_candidates: list[Any] = []
    out_of_list_accepted_count = 0
    for accepted_id in accepted_ids:
        if accepted_id in current_by_id:
            panel_candidates.append(current_by_id[accepted_id])
            continue

        public_item = public_items.get(accepted_id)
        if public_item is not None:
            panel_candidates.append(candidate_from_public_item(public_item, item_id=item.id))
            out_of_list_accepted_count += 1
            continue

        demo_candidate = demo_data.get_candidate(accepted_id)
        if demo_candidate is not None and demo_candidate.item_id == item.id:
            panel_candidates.append(demo_candidate)
            out_of_list_accepted_count += 1

    estimate = build_estimate_panel(item, item_decisions, candidates=panel_candidates)
    return estimate, out_of_list_accepted_count


@require_POST
def decide(request, candidate_id):
    from ingestion.models import PublicItem

    item_id_raw = request.POST.get("item_id")
    if item_id_raw is not None and item_id_raw != "":
        try:
            requested_item_id = int(item_id_raw)
        except ValueError as exc:
            raise Http404("Item not found") from exc
    else:
        requested_item_id = None

    pi = PublicItem.objects.filter(pk=candidate_id).prefetch_related("raw_records").first()
    if pi is not None:
        candidate = candidate_from_public_item(pi, item_id=requested_item_id)
    else:
        candidate = demo_data.get_candidate(candidate_id)

    if candidate is None:
        raise Http404("Candidate not found")

    decision = request.POST.get("decision")
    if decision not in ["accept", "reject"]:
        return HttpResponseBadRequest(b"Invalid decision")

    item_id = (
        requested_item_id if requested_item_id is not None else getattr(candidate, "item_id", None)
    )
    if item_id is None:
        return HttpResponseBadRequest(b"Requested item is required")

    item = get_item(item_id)
    if item is None:
        raise Http404("Item not found")
    item_unit = item.unit

    if pi is not None:
        fetch_awarded_price_on_demand(pi)
        candidate = candidate_from_public_item(pi, item_id=item_id)

    decisions = request.session.get("screening_decisions", {})
    dec_key = f"{item_id}:{candidate_id}"
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

    item_decisions = _parse_item_decisions(decisions, item_id)
    estimate, _ = build_item_estimate_panel(item, item_decisions, current_candidates=[candidate])

    return render(
        request,
        "pricing/_candidate_decision.html",
        {
            "candidate": candidate,
            "decision": decision,
            "proximity": proximity,
            "expected_price": expected_price,
            "item_unit": item_unit,
            "item_id": item.id,
            "estimate": estimate,
            "oob_estimate": estimate,
        },
    )


def screening(request, item_id):
    """Render item price screening; caches fetched PNCP RawRecords and awarded prices on GET."""
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
        limit=MAX_SCREENING_CANDIDATES,
    )

    raw_decisions = request.session.get("screening_decisions", {})
    decisions = _parse_item_decisions(raw_decisions, item_id)
    estimate, out_of_list_accepted_count = build_item_estimate_panel(
        item, decisions, current_candidates=candidates
    )

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

    if corpus_info_function is not get_corpus_info or search_function is default_search_function:
        corpus_info = corpus_info_function()
    else:
        corpus_info = None

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
            "out_of_list_accepted_count": out_of_list_accepted_count,
            "corpus_info": corpus_info,
        },
    )
