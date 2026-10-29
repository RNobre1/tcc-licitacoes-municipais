from django.http import Http404
from django.shortcuts import render

from . import demo_data


def home(request):
    return render(request, "procurement/home.html")


def procurement_list(request):
    procurements = demo_data.list_procurements()
    return render(request, "procurement/procurement_list.html", {"procurements": procurements})


def procurement_detail(request, procurement_id: int):
    procurement = demo_data.get_procurement(procurement_id)
    if procurement is None:
        raise Http404
    return render(request, "procurement/procurement_detail.html", {"procurement": procurement})
