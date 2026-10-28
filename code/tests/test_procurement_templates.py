from dataclasses import dataclass
from decimal import Decimal

import pytest
from django.conf import settings
from django.template.loader import render_to_string
from django.test import RequestFactory


@dataclass(frozen=True)
class ItemStub:
    id: int
    description: str
    quantity: Decimal
    unit: str
    requesting_department: str


@dataclass(frozen=True)
class ProcurementStub:
    id: int
    title: str
    items: tuple[ItemStub, ...] = ()


pytestmark = pytest.mark.urls("tests.urls")


def _render_procurement_list(procurements: list[ProcurementStub]) -> str:
    request = RequestFactory().get("/procurements/")
    return render_to_string(
        "procurement/procurement_list.html",
        {"procurements": procurements},
        request=request,
    )


def _render_procurement_detail(procurement: ProcurementStub) -> str:
    request = RequestFactory().get(f"/procurements/{procurement.id}/")
    return render_to_string(
        "procurement/procurement_detail.html",
        {"procurement": procurement},
        request=request,
    )


def test_procurement_list_extends_base_and_sets_the_page_title():
    rendered = _render_procurement_list([])
    assert f"<title>Processos de contratação — {settings.SYSTEM_NAME}</title>" in rendered


def test_procurement_list_renders_each_title():
    p1 = ProcurementStub(id=1, title="Aquisição de merenda escolar")
    p2 = ProcurementStub(id=2, title="Reforma da Unidade Básica de Saúde")
    rendered = _render_procurement_list([p1, p2])

    assert "Aquisição de merenda escolar" in rendered
    assert "Reforma da Unidade Básica de Saúde" in rendered
    assert "Nenhum processo de contratação encontrado." not in rendered


def test_procurement_list_links_each_procurement_to_detail():
    p1 = ProcurementStub(id=7, title="Aquisição de merenda escolar")
    p2 = ProcurementStub(id=3, title="Reforma da Unidade Básica de Saúde")
    rendered = _render_procurement_list([p1, p2])

    assert 'href="/procurements/7/"' in rendered
    assert 'href="/procurements/3/"' in rendered


def test_procurement_list_renders_empty_message_when_no_procurements():
    rendered = _render_procurement_list([])

    assert "Nenhum processo de contratação encontrado." in rendered


def test_procurement_detail_extends_base_and_sets_the_page_title():
    procurement = ProcurementStub(id=1, title="Material de expediente")
    rendered = _render_procurement_detail(procurement)
    assert f"<title>Material de expediente — {settings.SYSTEM_NAME}</title>" in rendered


def test_procurement_detail_renders_title_in_h1():
    procurement = ProcurementStub(id=1, title="Aquisição de merenda escolar")
    rendered = _render_procurement_detail(procurement)

    assert "<h1>Aquisição de merenda escolar</h1>" in rendered


def test_procurement_detail_renders_all_item_fields_in_table():
    item1 = ItemStub(
        id=101,
        description="Resma de papel A4",
        quantity=Decimal("50"),
        unit="pacote",
        requesting_department="Secretaria Municipal de Educação",
    )
    item2 = ItemStub(
        id=102,
        description="Caneta esferográfica azul",
        quantity=Decimal("200"),
        unit="caixa",
        requesting_department="Secretaria Municipal de Saúde",
    )
    procurement = ProcurementStub(
        id=1,
        title="Material de expediente",
        items=(item1, item2),
    )
    rendered = _render_procurement_detail(procurement)

    assert "<table>" in rendered
    flat = " ".join(rendered.split())
    assert (
        "<th>Descrição</th> <th>Quantidade</th> <th>Unidade</th> <th>Secretaria demandante</th>"
        in flat
    )
    for item in (item1, item2):
        assert (
            f"<td>{item.description}</td> <td>{item.quantity}</td> "
            f"<td>{item.unit}</td> <td>{item.requesting_department}</td>"
        ) in flat


def test_procurement_detail_renders_back_link_to_list():
    procurement = ProcurementStub(id=1, title="Material de expediente")
    rendered = _render_procurement_detail(procurement)

    assert 'href="/procurements/"' in rendered
