from django.http import HttpResponse
from django.urls import include, path


def _stub_view(request, *args, **kwargs):
    return HttpResponse("")


procurement_patterns = (
    [
        path("procurements/", _stub_view, name="list"),
        path("procurements/<int:procurement_id>/", _stub_view, name="detail"),
    ],
    "procurement",
)

urlpatterns = [
    path("", include(procurement_patterns)),
]
