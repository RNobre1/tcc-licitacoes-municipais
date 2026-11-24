import concurrent.futures
import re
import time
import urllib.error
from collections.abc import Callable
from datetime import datetime, timedelta
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

ITEM_ENDPOINT_PATTERN = re.compile(
    r"^/api/pncp/v1/orgaos/(?P<cnpj>\d+)/compras/(?P<ano>\d+)/(?P<seq>\d+)/itens$"
)


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
            default=None,
            help="Federative Unit code (default: None for all states / national search)",
        )
        parser.add_argument(
            "--modality",
            nargs="*",
            default=[6, 8, 7],
            help="Procurement modality code(s), e.g. 6 8 7 (default: 6 8 7)",
        )
        parser.add_argument(
            "--concurrency",
            type=int,
            default=3,
            help="Number of concurrent item-fetching threads (1 to 4, default: 3)",
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
            start_dt = datetime.strptime(start_str, "%Y-%m-%d").date()
            end_dt = datetime.strptime(end_str, "%Y-%m-%d").date()
        except ValueError as exc:
            raise CommandError("Dates must be in YYYY-MM-DD format") from exc

        if start_dt > end_dt:
            raise CommandError("Start date cannot be after end date")

        uf = options.get("uf")
        raw_mod = options.get("modality")
        if raw_mod is None:
            modalities = [6, 8, 7]
        elif isinstance(raw_mod, int):
            modalities = [raw_mod]
        elif isinstance(raw_mod, str):
            modalities = [int(p) for p in raw_mod.replace(",", " ").split()]
        elif isinstance(raw_mod, list):
            modalities = []
            for item in raw_mod:
                if isinstance(item, int):
                    modalities.append(item)
                elif isinstance(item, str):
                    for part in item.replace(",", " ").split():
                        modalities.append(int(part))
            if not modalities:
                modalities = [6, 8, 7]
        else:
            modalities = [6, 8, 7]

        concurrency = max(1, min(4, int(options.get("concurrency") or 3)))
        base_url = options.get("base_url", DEFAULT_PNCP_BASE_URL)
        with_results = bool(options.get("with_results"))
        transport = options.get("transport") or create_retrying_transport()

        start_time = time.monotonic()

        self.stdout.write(
            f"Fetching PNCP publications from {start_str} to {end_str} "
            f"(UF={uf or 'ALL'}, modalities={modalities}, concurrency={concurrency})..."
        )

        existing_purchases: set[tuple[str, int, int]] | None = None

        def _get_existing_purchases() -> set[tuple[str, int, int]]:
            nonlocal existing_purchases
            if existing_purchases is None:
                existing_purchases = set()
                for ep in (
                    RawRecord.objects.filter(endpoint__startswith="/api/pncp/v1/orgaos/")
                    .filter(endpoint__endswith="/itens")
                    .values_list("endpoint", flat=True)
                    .iterator(chunk_size=2000)
                ):
                    m = ITEM_ENDPOINT_PATTERN.match(ep)
                    if m:
                        existing_purchases.add(
                            (m.group("cnpj"), int(m.group("ano")), int(m.group("seq")))
                        )
            return existing_purchases

        publications_count = 0
        item_pages_count = 0
        items_count = 0
        results_count = 0
        skipped_already_stored = 0
        failures_count = 0

        # Walk day by day
        current_dt = start_dt
        while current_dt <= end_dt:
            day_str = current_dt.strftime("%Y%m%d")

            for mod in modalities:
                pub_params: dict[str, Any] = {
                    "dataInicial": day_str,
                    "dataFinal": day_str,
                    "codigoModalidadeContratacao": mod,
                }
                if uf:
                    pub_params["uf"] = uf

                try:
                    pub_records = fetch_publications(
                        params=pub_params,
                        transport=transport,
                        base_url=base_url,
                        save=True,
                    )
                except Exception as exc:
                    raise CommandError(f"Failed to fetch publications from PNCP: {exc}") from exc

                all_publications: list[dict[str, Any]] = []
                for pub_record in pub_records:
                    data = pub_record.payload.get("data", [])
                    if isinstance(data, list):
                        all_publications.extend(data)

                publications_count += len(all_publications)

                pubs_to_fetch: list[dict[str, Any]] = []
                for pub in all_publications:
                    cnpj = pub.get("orgaoEntidade", {}).get("cnpj")
                    ano = pub.get("anoCompra")
                    sequencial = pub.get("sequencialCompra")
                    controle = pub.get("numeroControlePNCP", "unknown")

                    if not cnpj or not ano or sequencial is None:
                        self.stderr.write(
                            f"Skipping publication with missing identification: {controle}"
                        )
                        failures_count += 1
                        continue

                    purchase_key = (str(cnpj), int(ano), int(sequencial))
                    if purchase_key in _get_existing_purchases():
                        skipped_already_stored += 1
                        continue

                    pubs_to_fetch.append(pub)

                # Fetch items for pending publications using worker pool
                def _fetch_single_pub(pub_data: dict[str, Any]):
                    c = str(pub_data.get("orgaoEntidade", {}).get("cnpj"))
                    a = int(pub_data.get("anoCompra"))
                    s = int(pub_data.get("sequencialCompra"))
                    ctrl = pub_data.get("numeroControlePNCP", f"{c}/{a}/{s}")

                    try:
                        it_records = fetch_items(
                            cnpj=c,
                            ano=a,
                            sequencial=s,
                            transport=transport,
                            base_url=base_url,
                            save=False,
                        )
                        it_count = sum(
                            len(r.payload) for r in it_records if isinstance(r.payload, list)
                        )

                        res_recs: list[RawRecord] = []
                        if with_results:
                            items_for_pub: list[dict[str, Any]] = []
                            for r in it_records:
                                if isinstance(r.payload, list):
                                    items_for_pub.extend(r.payload)
                            for it in items_for_pub:
                                if it.get("temResultado") is True:
                                    num_it = it.get("numeroItem")
                                    if num_it is not None:
                                        res_rec = fetch_item_results(
                                            cnpj=c,
                                            ano=a,
                                            sequencial=s,
                                            numero_item=int(num_it),
                                            transport=transport,
                                            base_url=base_url,
                                            save=False,
                                        )
                                        res_recs.append(res_rec)

                        return (c, a, s, it_records, it_count, res_recs, None, ctrl)
                    except PncpError as exc:
                        return (c, a, s, [], 0, [], exc, ctrl)
                    except Exception as exc:
                        return (c, a, s, [], 0, [], exc, ctrl)

                if pubs_to_fetch:
                    if concurrency == 1:
                        results = [_fetch_single_pub(p) for p in pubs_to_fetch]
                    else:
                        with concurrent.futures.ThreadPoolExecutor(
                            max_workers=concurrency
                        ) as executor:
                            results = list(executor.map(_fetch_single_pub, pubs_to_fetch))

                    records_to_save: list[RawRecord] = []
                    for c, a, s, it_recs, it_cnt, res_recs, err, ctrl in results:
                        if err is not None:
                            self.stderr.write(
                                f"Skipping publication {ctrl} due to items error: {err}"
                            )
                            failures_count += 1
                        else:
                            records_to_save.extend(it_recs)
                            records_to_save.extend(res_recs)
                            _get_existing_purchases().add((c, a, s))
                            item_pages_count += len(it_recs)
                            items_count += it_cnt
                            results_count += len(res_recs)

                    if records_to_save:
                        with transaction.atomic():
                            RawRecord.objects.bulk_create(records_to_save)

            current_dt += timedelta(days=1)

        elapsed = time.monotonic() - start_time

        self.stdout.write("\n--- Ingestion Summary ---")
        self.stdout.write(f"Publications: {publications_count}")
        self.stdout.write(f"Item pages: {item_pages_count}")
        self.stdout.write(f"Items: {items_count}")
        self.stdout.write(f"Skipped already stored: {skipped_already_stored}")
        if with_results:
            self.stdout.write(f"Item results: {results_count}")
        self.stdout.write(f"Failures: {failures_count}")
        self.stdout.write(f"Elapsed: {elapsed:.2f}s")
