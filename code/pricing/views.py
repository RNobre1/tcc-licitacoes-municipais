from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.http import require_POST

from . import demo_data


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

    return render(
        request, "pricing/_candidate.html", {"candidate": candidate, "decision": decision}
    )
