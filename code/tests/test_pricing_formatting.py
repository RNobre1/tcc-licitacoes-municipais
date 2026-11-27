from decimal import Decimal

import pytest
from django.template import Context, Template

from pricing.formatting import format_decimal, format_similarity


@pytest.mark.parametrize(
    "value,expected",
    [
        (Decimal("41.1400"), "41,14"),
        (Decimal("17.55"), "17,55"),
        (Decimal("17.5500"), "17,55"),
        (17.55, "17,55"),
        (Decimal("0.0450"), "0,0450"),
        (Decimal("0.045"), "0,0450"),
        (0.045, "0,0450"),
        (Decimal("0.0005"), "0,0005"),
        (Decimal("0.0001"), "0,0001"),
        (Decimal("50.0000"), "50"),
        (Decimal("28.00"), "28"),
        (Decimal("1000.0000"), "1000"),
        (50, "50"),
        (Decimal("24.80"), "24,80"),
        (Decimal("24.8"), "24,80"),
        (Decimal("25.50"), "25,50"),
        (Decimal("0"), "0"),
        (Decimal("0.0000"), "0"),
        (Decimal("-0.00"), "0"),
        (Decimal("1.23456"), "1,23456"),
        (Decimal("0.00005"), "0,00005"),
        (Decimal("1.23456700"), "1,234567"),
        (Decimal("-24.8"), "-24,80"),
        (None, "—"),
        ("invalid", "invalid"),
        (Decimal("NaN"), "NaN"),
        (Decimal("Infinity"), "Infinity"),
        (float("inf"), "inf"),
    ],
)
def test_format_decimal_rules(value, expected):
    assert format_decimal(value) == expected


def test_format_decimal_never_rounds_many_decimals():
    value = Decimal("12.345678901234567890123456789012")
    assert format_decimal(value) == "12,345678901234567890123456789012"


def test_format_decimal_template_filter():
    tpl = Template("{% load pricing_extras %}{{ val|format_decimal }}")
    assert tpl.render(Context({"val": Decimal("41.1400")})) == "41,14"
    assert tpl.render(Context({"val": Decimal("50.0000")})) == "50"
    assert tpl.render(Context({"val": None})) == "—"


@pytest.mark.parametrize(
    "value,expected",
    [
        (0.89414424, "0,89"),
        (0.895, "0,90"),
        (0.885, "0,89"),
        (0.145, "0,15"),
        (1.0, "1,00"),
        (0.5, "0,50"),
        (0.0, "0,00"),
        (None, "—"),
        (Decimal("0.885"), "0,89"),
        (Decimal("0.895"), "0,90"),
        (Decimal("0.89414424"), "0,89"),
        (Decimal("-0.00"), "0,00"),
        ("invalid", "invalid"),
        (Decimal("NaN"), "NaN"),
        (float("inf"), "inf"),
    ],
)
def test_format_similarity_rules(value, expected):
    assert format_similarity(value) == expected


def test_format_similarity_template_filter():
    tpl = Template("{% load pricing_extras %}{{ val|format_similarity }}")
    assert tpl.render(Context({"val": 0.89414424})) == "0,89"
    assert tpl.render(Context({"val": 0.885})) == "0,89"
    assert tpl.render(Context({"val": 0.895})) == "0,90"
    assert tpl.render(Context({"val": 0.145})) == "0,15"
    assert tpl.render(Context({"val": 0.5})) == "0,50"
    assert tpl.render(Context({"val": 1.0})) == "1,00"
    assert tpl.render(Context({"val": 0.0})) == "0,00"
    assert tpl.render(Context({"val": None})) == "—"
