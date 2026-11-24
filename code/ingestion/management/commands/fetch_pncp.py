import time
import urllib.error
from collections.abc import Callable
from datetime import datetime
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from ingestion.client import (
    DEFAULT_PNCP_BASE_URL,
    PncpError,
    PncpResponseError,
    TransportCallable,
    fetch_item_results,
    fetch_items,
    fetch_publications,
    urllib_transport,
)
from ingestion.models import RawRecord


class RetryingTransport:
    """Transport wrapper with exponential backoff on 5xx and timeouts."""

    def __init__(
        self,
        base_transport: TransportCallable | None = None,
        max_attempts: int = 5,
        backoff_factor: float = 1.0,
        sleep_func: Callable[[float], None] | None = None,
    ) -> None:
        self.base_transport = base_transport or urllib_transport
        self.max_attempts = max_attempts
        self.backoff_factor = backoff_factor
        self.sleep_func = sleep_func or time.sleep

    def __call__(self, url: str, params: dict[str, Any] | None = None) -> tuple[int, Any]:
        attempt = 1
        while True:
            try:
                status, data = self.base_transport(url, params)
                if status < 500 or attempt >= self.max_attempts:
                    return status, data
            except (TimeoutError, urllib.error.URLError, PncpResponseError) as exc:
                if attempt >= self.max_attempts:
                    raise
                if isinstance(exc, urllib.error.HTTPError) and exc.code < 500:
                    raise
                if (
                    isinstance(exc, PncpResponseError)
                    and exc.status is not None
                    and exc.status < 500
                ):
                    raise

            # Retry with exponential backoff
            sleep_duration = self.backoff_factor * (2 ** (attempt - 1))
            if sleep_duration > 0:
                self.sleep_func(sleep_duration)
            attempt += 1


def create_retrying_transport(
    base_transport: TransportCallable | None = None,
    max_attempts: int = 5,
    backoff_factor: float = 1.0,
    sleep_func: Callable[[float], None] | None = None,
) -> RetryingTransport:
    return RetryingTransport(
        base_transport=base_transport,
        max_attempts=max_attempts,
        backoff_factor=backoff_factor,
        sleep_func=sleep_func,
    )


class Command(BaseCommand):
    help = "Fetch public procurement publications and items from PNCP API."
    stealth_options = ("transport",)

    def add_arguments(self, parser):
        parser.add_argument(
            "--start",
            required=True,
            help="Start date in YYYY-MM-DD format",
        )
        parser.add_argument(
            "--end",
            required=True,
            help="End date in YYYY-MM-DD format",
        )
        parser.add_argument(
            "--uf",
            default="PA",
            help="Federative Unit code (default: PA)",
        )
        parser.add_argument(
            "--modality",
            type=int,
            default=6,
            help="Procurement modality code (default: 6 for Pregão Eletrônico)",
        )
        parser.add_argument(
            "--base-url",
            default=DEFAULT_PNCP_BASE_URL,
            help="Base URL for PNCP API",
        )
        parser.add_argument(
            "--with-results",
            action="store_true",
            default=False,
            help="Fetch item results for items with temResultado=True",
        )

    def handle(self, *args, **options):
        start_str = options["start"]
        end_str = options["end"]

        try:
            start_dt = datetime.strptime(start_str, "%Y-%m-%d")
            end_dt = datetime.strptime(end_str, "%Y-%m-%d")
        except ValueError as exc:
            raise CommandError("Dates must be in YYYY-MM-DD format") from exc

        if start_dt > end_dt:
            raise CommandError("Start date cannot be after end date")

        data_inicial = start_dt.strftime("%Y%m%d")
        data_final = end_dt.strftime("%Y%m%d")
        uf = options.get("uf")
        modality = options.get("modality")
        base_url = options.get("base_url", DEFAULT_PNCP_BASE_URL)
        with_results = bool(options.get("with_results"))

        transport = options.get("transport") or create_retrying_transport()

        start_time = time.monotonic()

        pub_params: dict[str, Any] = {
            "dataInicial": data_inicial,
            "dataFinal": data_final,
        }
        if uf:
            pub_params["uf"] = uf
        if modality:
            pub_params["codigoModalidadeContratacao"] = modality

        self.stdout.write(
            f"Fetching PNCP publications from {start_str} to {end_str} "
            f"(UF={uf}, modality={modality})..."
        )

        try:
            publication_records = fetch_publications(
                params=pub_params,
                transport=transport,
                base_url=base_url,
                save=True,
            )
        except Exception as exc:
            raise CommandError(f"Failed to fetch publications from PNCP: {exc}") from exc

        publications_count = 0
        item_pages_count = 0
        items_count = 0
        results_count = 0
        failures_count = 0

        # Extract publications from pages
        all_publications: list[dict[str, Any]] = []
        for pub_record in publication_records:
            data = pub_record.payload.get("data", [])
            if isinstance(data, list):
                all_publications.extend(data)

        publications_count = len(all_publications)
        self.stdout.write(f"Retrieved {publications_count} publications. Fetching items...")

        for pub in all_publications:
            cnpj = pub.get("orgaoEntidade", {}).get("cnpj")
            ano = pub.get("anoCompra")
            sequencial = pub.get("sequencialCompra")
            controle = pub.get("numeroControlePNCP", "unknown")

            if not cnpj or not ano or sequencial is None:
                self.stderr.write(f"Skipping publication with missing identification: {controle}")
                failures_count += 1
                continue

            try:
                if with_results:
                    item_records = fetch_items(
                        cnpj=str(cnpj),
                        ano=int(ano),
                        sequencial=int(sequencial),
                        transport=transport,
                        base_url=base_url,
                        save=False,
                    )
                    items_for_pub: list[dict[str, Any]] = []
                    for item_record in item_records:
                        if isinstance(item_record.payload, list):
                            items_for_pub.extend(item_record.payload)

                    result_records: list[RawRecord] = []
                    for item in items_for_pub:
                        if item.get("temResultado") is True:
                            numero_item = item.get("numeroItem")
                            if numero_item is not None:
                                res_rec = fetch_item_results(
                                    cnpj=str(cnpj),
                                    ano=int(ano),
                                    sequencial=int(sequencial),
                                    numero_item=int(numero_item),
                                    transport=transport,
                                    base_url=base_url,
                                    save=False,
                                )
                                result_records.append(res_rec)

                    with transaction.atomic():
                        RawRecord.objects.bulk_create(item_records + result_records)

                    item_pages_count += len(item_records)
                    items_count += len(items_for_pub)
                    results_count += len(result_records)
                else:
                    item_records = fetch_items(
                        cnpj=str(cnpj),
                        ano=int(ano),
                        sequencial=int(sequencial),
                        transport=transport,
                        base_url=base_url,
                        save=True,
                    )
                    item_pages_count += len(item_records)
                    for item_record in item_records:
                        if isinstance(item_record.payload, list):
                            items_count += len(item_record.payload)
            except PncpError as exc:
                self.stderr.write(f"Skipping publication {controle} due to items error: {exc}")
                failures_count += 1
            except Exception as exc:
                self.stderr.write(f"Skipping publication {controle} due to unexpected error: {exc}")
                failures_count += 1

        elapsed = time.monotonic() - start_time

        self.stdout.write("\n--- Ingestion Summary ---")
        self.stdout.write(f"Publications: {publications_count}")
        self.stdout.write(f"Item pages: {item_pages_count}")
        self.stdout.write(f"Items: {items_count}")
        if with_results:
            self.stdout.write(f"Item results: {results_count}")
        self.stdout.write(f"Failures: {failures_count}")
        self.stdout.write(f"Elapsed: {elapsed:.2f}s")
