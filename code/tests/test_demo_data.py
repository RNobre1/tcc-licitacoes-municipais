from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from procurement.demo_data import (
    UNITS,
    get_item,
    get_procurement,
    list_procurements,
)


def test_list_procurements_returns_three():
    procurements = list_procurements()
    assert len(procurements) == 3


def test_procurement_items_count_between_three_and_five():
    procurements = list_procurements()
    assert len(procurements) > 0
    for procurement in procurements:
        assert 3 <= len(procurement.items) <= 5


def test_multiple_requesting_departments():
    procurements = list_procurements()
    departments = {
        item.requesting_department for procurement in procurements for item in procurement.items
    }
    assert len(departments) >= 2


def test_item_units_belong_to_vocabulary():
    procurements = list_procurements()
    assert len(procurements) > 0
    for procurement in procurements:
        for item in procurement.items:
            assert item.unit in UNITS


def test_item_quantities_are_positive():
    procurements = list_procurements()
    assert len(procurements) > 0
    for procurement in procurements:
        for item in procurement.items:
            assert isinstance(item.quantity, Decimal)
            assert item.quantity > Decimal(0)


def test_item_ids_are_unique_across_procurements():
    procurements = list_procurements()
    item_ids = [item.id for procurement in procurements for item in procurement.items]
    assert len(item_ids) > 0
    assert len(item_ids) == len(set(item_ids))


def test_item_requested_by_multiple_departments_with_different_wording():
    item_1 = get_item(1)
    item_8 = get_item(8)
    assert item_1 is not None and item_8 is not None
    assert item_1.requesting_department != item_8.requesting_department
    assert item_1.description != item_8.description
    assert "papel" in item_1.description.lower() and "a4" in item_1.description.lower()
    assert "papel" in item_8.description.lower() and "a4" in item_8.description.lower()


def test_get_procurement_known_and_unknown():
    procurement = get_procurement(1)
    assert procurement is not None
    assert procurement.id == 1

    assert get_procurement(999) is None


def test_get_item_known_and_unknown():
    item = get_item(1)
    assert item is not None
    assert item.id == 1

    assert get_item(999) is None


def test_requested_item_and_procurement_are_frozen():
    procurement = get_procurement(1)
    assert procurement is not None
    with pytest.raises(FrozenInstanceError):
        procurement.title = "New title"  # type: ignore[misc]

    item = get_item(1)
    assert item is not None
    with pytest.raises(FrozenInstanceError):
        item.description = "New description"  # type: ignore[misc]
