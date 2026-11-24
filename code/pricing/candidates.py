from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any


def build_provenance_url(cnpj: str, year: int, purchase_sequence: int) -> str:
    """Build the public PNCP purchase page URL from PNCP key components."""
    return f"https://pncp.gov.br/app/editais/{cnpj}/{year}/{purchase_sequence}"


@dataclass(frozen=True)
class Candidate:
    """A price candidate built from a normalized PublicItem."""

    id: int
    description: str
    unit: str
    quantity: Decimal
    agency: str
    date: date
    source: str = "PNCP"
    provenance: str = ""
    similarity: float = 0.0
    awarded_unit_price: Decimal | None = None
    estimated_unit_price: Decimal | None = None
    secret_budget: bool = False
    item_id: int | None = None

    @property
    def published_on(self) -> date:
        return self.date

    @property
    def price(self) -> Decimal | None:
        """Display price: awarded when present, else estimated if not secret budget."""
        if self.secret_budget:
            return None
        if self.awarded_unit_price is not None and self.awarded_unit_price > Decimal("0.00"):
            return self.awarded_unit_price
        if self.estimated_unit_price is not None and self.estimated_unit_price > Decimal("0.00"):
            return self.estimated_unit_price
        return None

    @property
    def is_estimated(self) -> bool:
        """Return True when displaying estimated price instead of awarded."""
        if self.secret_budget:
            return False
        has_awarded = self.awarded_unit_price is not None and self.awarded_unit_price > Decimal(
            "0.00"
        )
        has_estimated = (
            self.estimated_unit_price is not None and self.estimated_unit_price > Decimal("0.00")
        )
        return not has_awarded and has_estimated

    @property
    def price_kind(self) -> str:
        """Price classification: 'awarded', 'estimated', or 'secret_budget'."""
        if self.secret_budget:
            return "secret_budget"
        if self.awarded_unit_price is not None and self.awarded_unit_price > Decimal("0.00"):
            return "awarded"
        if self.estimated_unit_price is not None and self.estimated_unit_price > Decimal("0.00"):
            return "estimated"
        return "secret_budget"

    @property
    def usable_calculation_price(self) -> Decimal | None:
        """Price usable for estimation calculation: awarded prices only.

        Estimated prices, zero prices, and secret budget items return None
        and never enter calculation.
        """
        if self.secret_budget or self.is_estimated:
            return None
        if self.awarded_unit_price is not None and self.awarded_unit_price > Decimal("0.00"):
            return self.awarded_unit_price
        return None

    @property
    def has_usable_calculation_price(self) -> bool:
        return self.usable_calculation_price is not None


def candidate_from_public_item(
    public_item: Any,
    similarity: float = 0.0,
    item_id: int | None = None,
) -> Candidate:
    """Build a Candidate instance from a PublicItem and search score."""
    provenance = build_provenance_url(
        cnpj=public_item.cnpj,
        year=public_item.year,
        purchase_sequence=public_item.purchase_sequence,
    )
    return Candidate(
        id=public_item.pk,
        description=public_item.description,
        unit=public_item.unit,
        quantity=public_item.quantity,
        agency=public_item.agency_name,
        date=public_item.published_on,
        source="PNCP",
        provenance=provenance,
        similarity=float(similarity),
        awarded_unit_price=public_item.awarded_unit_price,
        estimated_unit_price=public_item.estimated_unit_price,
        secret_budget=public_item.secret_budget,
        item_id=item_id,
    )
