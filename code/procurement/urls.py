from django.urls import path

from . import views

app_name = "procurement"

urlpatterns = [
    path("", views.home, name="home"),
    path("procurements/", views.procurement_list, name="list"),
    path("procurements/<int:procurement_id>/", views.procurement_detail, name="detail"),
]
