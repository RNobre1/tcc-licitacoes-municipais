from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.http import require_POST

from procurement.demo_data import get_item

from . import demo_data
from .ranking import compute_proximity, format_proximity, parse_expected_price, rank_candidates


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

    return render(
        request,
        "pricing/_candidate.html",
        {
            "candidate": candidate,
            "decision": decision,
            "proximity": proximity,
            "expected_price": expected_price,
        },
    )


def screening(request, item_id):
    item = get_item(item_id)
    if item is None:
        raise Http404("Item not found")

    raw_expected_price = request.GET.get("expected_price")
    expected_price = parse_expected_price(raw_expected_price)
    expected_price_ignored = bool(
        raw_expected_price and raw_expected_price.strip() and expected_price is None
    )

    candidates = rank_candidates(demo_data.candidates_for(item_id), expected_price, item.unit)

    decisions = {int(k): v for k, v in request.session.get("screening_decisions", {}).items()}

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
            "item": item,
            "candidates": candidates,
            "decisions": decisions,
            "proximities": proximities,
            "expected_price": expected_price,
            "expected_price_ignored": expected_price_ignored,
        },
    )
