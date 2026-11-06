from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.http import require_POST

from procurement.demo_data import get_item, get_procurement_for_item

from . import demo_data
from .estimation import calculate_mean, calculate_median, calculate_min, requires_justification
from .ranking import compute_proximity, format_proximity, parse_expected_price, rank_candidates


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


def build_estimate_panel(item, decisions: dict) -> dict:
    if item is None:
        return EstimatePanel(EMPTY_PANEL, counted_candidate_ids=set())

    candidates = demo_data.candidates_for(item.id)
    counted_candidate_ids = {
        candidate.id
        for candidate in candidates
        if decisions.get(candidate.id) == "accept" and candidate.unit == item.unit
    }
    prices = [candidate.price for candidate in candidates if candidate.id in counted_candidate_ids]

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
    candidate = demo_data.get_candidate(candidate_id)
    if candidate is None:
        raise Http404("Candidate not found")

    decision = request.POST.get("decision")
    if decision not in ["accept", "reject"]:
        return HttpResponseBadRequest(b"Invalid decision")

    decisions = request.session.get("screening_decisions", {})
    decisions[str(candidate_id)] = decision
    request.session["screening_decisions"] = decisions

    expected_price = parse_expected_price(request.POST.get("expected_price"))
    item = get_item(candidate.item_id)
    item_unit = item.unit if item else None
    prox = compute_proximity(candidate.price, expected_price, candidate.unit, item_unit)
    proximity = format_proximity(candidate.price, expected_price, prox, candidate.unit, item_unit)

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

    candidates = rank_candidates(demo_data.candidates_for(item_id), expected_price, item.unit)

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
        },
    )
