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

procurement_patterns = (
    [
        path("", _stub_view, name="home"),
        path("procurements/", _stub_view, name="list"),
        path("procurements/<int:procurement_id>/", _stub_view, name="detail"),
    ],
    "procurement",
)

urlpatterns = [
    path("", include(pricing_patterns)),
    path("", include(procurement_patterns)),
]
