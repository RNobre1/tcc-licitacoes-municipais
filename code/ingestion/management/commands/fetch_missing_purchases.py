import re
import time

from django.core.management.base import BaseCommand

from ingestion.client import PncpError, fetch_purchase
from ingestion.management.commands.fetch_pncp import create_retrying_transport
from ingestion.models import RawRecord

ITEM_ENDPOINT_PATTERN = re.compile(
    r"^/api/pncp/v1/orgaos/(?P<cnpj>\d+)/compras/(?P<ano>\d+)/(?P<seq>\d+)/itens$"
)
PURCHASE_ENDPOINT_PATTERN = re.compile(
    r"^/api/consulta/v1/orgaos/(?P<cnpj>\d+)/compras/(?P<ano>\d+)/(?P<seq>\d+)$"
)
PUB_ENDPOINT = "/api/consulta/v1/contratacoes/publicacao"


class Command(BaseCommand):
    help = "Fetch header metadata for purchases that have item pages but no publication record."

    def handle(self, *args, **options):
        start_time = time.monotonic()
        transport = create_retrying_transport()

        # 1. Identify all purchases with publication metadata
        known_purchases: set[tuple[str, int, int]] = set()
        for r in RawRecord.objects.filter(endpoint__startswith=PUB_ENDPOINT).iterator():
            if isinstance(r.payload, dict):
                for pub in r.payload.get("data", []):
                    cnpj = pub.get("orgaoEntidade", {}).get("cnpj")
                    ano = pub.get("anoCompra")
                    seq = pub.get("sequencialCompra")
                    if cnpj and ano is not None and seq is not None:
                        known_purchases.add((str(cnpj), int(ano), int(seq)))

        # Also check single purchase endpoints already fetched
        for r in RawRecord.objects.filter(
            endpoint__startswith="/api/consulta/v1/orgaos/"
        ).iterator():
            m = PURCHASE_ENDPOINT_PATTERN.match(r.endpoint)
            if m:
                known_purchases.add((m.group("cnpj"), int(m.group("ano")), int(m.group("seq"))))

        # 2. Find all purchases from items endpoints
        purchases_with_items: set[tuple[str, int, int]] = set()
        for r in RawRecord.objects.filter(endpoint__startswith="/api/pncp/v1/orgaos/").iterator():
            m = ITEM_ENDPOINT_PATTERN.match(r.endpoint)
            if m:
                purchases_with_items.add(
                    (m.group("cnpj"), int(m.group("ano")), int(m.group("seq")))
                )

        missing = sorted(purchases_with_items - known_purchases)
        self.stdout.write(
            f"Found {len(purchases_with_items)} purchases with items pages, "
            f"{len(missing)} missing publication metadata."
        )

        fetched_count = 0
        failures_count = 0

        for cnpj, ano, seq in missing:
            try:
                fetch_purchase(
                    cnpj=cnpj,
                    ano=ano,
                    sequencial=seq,
                    transport=transport,
                    save=True,
                )
                fetched_count += 1
            except PncpError as exc:
                self.stderr.write(f"Failed to fetch purchase {cnpj}/{ano}/{seq}: {exc}")
                failures_count += 1
            except Exception as exc:
                self.stderr.write(f"Unexpected error for purchase {cnpj}/{ano}/{seq}: {exc}")
                failures_count += 1

        elapsed = time.monotonic() - start_time
        self.stdout.write(
            f"Completed: {fetched_count} fetched, {failures_count} failures in {elapsed:.2f}s."
        )
