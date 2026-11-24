from decimal import Decimal

from django.db import models


class RawRecord(models.Model):
    endpoint = models.TextField()
    params = models.JSONField(default=dict, blank=True)
    fetched_at = models.DateTimeField()
    payload = models.JSONField()
    status_code = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.endpoint} at {self.fetched_at}"


class PublicItem(models.Model):
    """Normalized public item from PNCP records."""

    cnpj = models.CharField(max_length=14, db_index=True)
    year = models.PositiveIntegerField()
    purchase_sequence = models.PositiveIntegerField()
    item_number = models.PositiveIntegerField()

    description = models.TextField()
    unit = models.CharField(max_length=50)
    quantity = models.DecimalField(max_digits=14, decimal_places=4)
    estimated_unit_price = models.DecimalField(max_digits=14, decimal_places=4)
    awarded_unit_price = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    secret_budget = models.BooleanField(default=False)
    published_on = models.DateField(db_index=True)
    agency_name = models.TextField()
    agency_cnpj = models.CharField(max_length=14)
    state = models.CharField(max_length=2, db_index=True)
    modality = models.PositiveIntegerField()
    item_kind = models.CharField(max_length=10, db_index=True)

    raw_records = models.ManyToManyField("ingestion.RawRecord", related_name="public_items")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cnpj", "year", "purchase_sequence", "item_number"],
                name="unique_pncp_item",
            )
        ]

    def __str__(self) -> str:
        return (
            f"PublicItem {self.cnpj}/{self.year}/{self.purchase_sequence}/"
            f"item {self.item_number}: {self.description[:40]}"
        )

    @property
    def pncp_key(self) -> tuple[str, int, int, int]:
        return (self.cnpj, self.year, self.purchase_sequence, self.item_number)

    @property
    def ano(self) -> int:
        return self.year

    @property
    def sequencial(self) -> int:
        return self.purchase_sequence

    @property
    def numero_item(self) -> int:
        return self.item_number

    @property
    def numeroItem(self) -> int:
        return self.item_number

    @property
    def has_usable_estimated_price(self) -> bool:
        """Return False if secret_budget is True or estimated_unit_price <= 0."""
        return not self.secret_budget and self.estimated_unit_price > Decimal("0.00")

    @property
    def usable_estimated_unit_price(self) -> Decimal | None:
        """Return estimated_unit_price if usable, else None.

        An item with secret_budget, whose estimated price is zero, must never reach
        estimation calculations as a candidate price.
        """
        return self.estimated_unit_price if self.has_usable_estimated_price else None
