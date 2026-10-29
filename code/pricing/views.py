from django.http import Http404
from django.shortcuts import render

from . import demo_data


def decide(request, candidate_id):
    decision = request.POST.get("decision")
    candidate = demo_data.get_candidate(candidate_id)

    if candidate is None:
        raise Http404("Candidate not found")

    decisions = request.session.get("screening_decisions", {})
    decisions[str(candidate_id)] = decision
    request.session["screening_decisions"] = decisions

    return render(
        request, "pricing/_candidate.html", {"candidate": candidate, "decision": decision}
    )
