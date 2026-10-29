from django.urls import path

from . import views

app_name = "pricing"

urlpatterns: list[object] = [
    path("candidates/<int:candidate_id>/decision/", views.decide, name="decide")
]
