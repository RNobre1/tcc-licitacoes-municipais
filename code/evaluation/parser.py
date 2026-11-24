"""Parser for QuotationReport documents."""

from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ChosenPriceReport:
    price_number: int
    source_category: str
    calculation_method: str
    unit_price: Decimal
    agency: str
    date: str
    chosen_description: str
    source: str
    identifier: str | None = None
    item_number_raw: str | None = None
    pncp_key: dict[str, Any] | None = None
    state: str | None = None
    modality: str | None = None
    unit: str | None = None
    quantity: str | None = None


@dataclass(frozen=True)
class RequestedItemReport:
    item_number: int
    short_description: str
    description: str
    unit: str
    quantity: Decimal
    estimated_unit_price: Decimal
    estimation_method: str
    chosen_prices: tuple[ChosenPriceReport, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class QuotationReport:
    report_id: str
    title: str
    survey_start: str | None
    survey_end: str | None
    generated_at: str | None
    items: tuple[RequestedItemReport, ...] = field(default_factory=tuple)


def extract_pdf_layout_text(pdf_path: Path) -> str:
    raise NotImplementedError


def parse_quotation_report_text(text: str, report_id: str = "") -> QuotationReport:
    raise NotImplementedError
