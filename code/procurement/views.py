from django.http.response import Http404
from django.shortcuts import render

from . import demo_data


def home(request):
    return render(request, "procurement/home.html")


def procurement_list(request):
    procurements = demo_data.list_procurements()
    return render(request, "procurement/procurement_list.html", {"procurements": procurements})


def procurement_detail(request, procurement_id: int):
    # Placeholder
    raise Http404
