from django.http import HttpResponse
from django.urls import include, path


def _stub_view(request, *args, **kwargs):
    return HttpResponse("")


pricing_patterns = (
    [
        path("items/<int:item_id>/screening/", _stub_view, name="screening"),
        path("candidates/<int:candidate_id>/decision/", _stub_view, name="decide"),
    ],
    "pricing",
)

urlpatterns = [
    path("", include(pricing_patterns)),
]
