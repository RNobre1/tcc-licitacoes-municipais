"""Demo data for procurement prototype."""

from dataclasses import dataclass
from decimal import Decimal

UNITS: tuple[str, ...] = (
    "caixa",
    "pacote",
    "quilograma",
    "unidade",
)


@dataclass(frozen=True)
class RequestedItem:
    id: int
    description: str
    quantity: Decimal
    unit: str
    requesting_department: str


@dataclass(frozen=True)
class Procurement:
    id: int
    title: str
    items: tuple[RequestedItem, ...]


_PROCUREMENTS: tuple[Procurement, ...] = (
    Procurement(
        id=1,
        title="Aquisição de materiais de escritório e expediente",
        items=(
            RequestedItem(
                id=1,
                description="Papel sulfite A4 branco, resma com 500 folhas",
                quantity=Decimal("100"),
                unit="pacote",
                requesting_department="Secretaria Municipal de Educação",
            ),
            RequestedItem(
                id=2,
                description="Caneta esferográfica azul com ponta média 1.0mm",
                quantity=Decimal("500"),
                unit="unidade",
                requesting_department="Secretaria Municipal de Educação",
            ),
            RequestedItem(
                id=3,
                description="Grampeador de mesa metálico para até 30 folhas",
                quantity=Decimal("20"),
                unit="unidade",
                requesting_department="Secretaria Municipal de Administração",
            ),
            RequestedItem(
                id=4,
                description="Clips de aço niquelado 2/0, caixa com 100 unidades",
                quantity=Decimal("50"),
                unit="caixa",
                requesting_department="Secretaria Municipal de Administração",
            ),
            RequestedItem(
                id=8,
                description="Papel A4 branco para impressão, pacote de 500 folhas",
                quantity=Decimal("80"),
                unit="pacote",
                requesting_department="Secretaria Municipal de Administração",
            ),
        ),
    ),
    Procurement(
        id=2,
        title="Aquisição de gêneros alimentícios e insumos para copa",
        items=(
            RequestedItem(
                id=5,
                description="Café torrado e moído tradicional, embalagem de 500g",
                quantity=Decimal("80"),
                unit="pacote",
                requesting_department="Secretaria Municipal de Administração",
            ),
            RequestedItem(
                id=6,
                description="Açúcar cristal branco refinado",
                quantity=Decimal("120"),
                unit="quilograma",
                requesting_department="Secretaria Municipal de Saúde",
            ),
            RequestedItem(
                id=7,
                description="Água mineral natural sem gás, garrafão de 20 litros",
                quantity=Decimal("60"),
                unit="unidade",
                requesting_department="Secretaria Municipal de Saúde",
            ),
        ),
    ),
    Procurement(
        id=3,
        title="Aquisição de materiais de limpeza e suprimentos complementares",
        items=(
            RequestedItem(
                id=9,
                description="Detergente líquido neutro biodegradável de 500ml",
                quantity=Decimal("150"),
                unit="unidade",
                requesting_department="Secretaria Municipal de Saúde",
            ),
            RequestedItem(
                id=10,
                description="Sabão em barra multiuso, pacote com 5 unidades de 200g",
                quantity=Decimal("40"),
                unit="pacote",
                requesting_department="Secretaria Municipal de Saúde",
            ),
            RequestedItem(
                id=11,
                description="Álcool etílico 70% líquido, frasco de 1 litro",
                quantity=Decimal("90"),
                unit="unidade",
                requesting_department="Secretaria Municipal de Saúde",
            ),
        ),
    ),
)


def list_procurements() -> list[Procurement]:
    return list(_PROCUREMENTS)


def get_procurement(procurement_id: int) -> Procurement | None:
    for procurement in _PROCUREMENTS:
        if procurement.id == procurement_id:
            return procurement
    return None


def get_item(item_id: int) -> RequestedItem | None:
    for procurement in _PROCUREMENTS:
        for item in procurement.items:
            if item.id == item_id:
                return item
    return None
