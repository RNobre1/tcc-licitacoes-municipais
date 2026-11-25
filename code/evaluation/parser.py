"""Parser for QuotationReport documents."""

import re
import subprocess
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any


class ParseError(Exception):
    """Raised when quotation report parsing encounters an invalid or unparseable layout."""


def parse_date_br(date_str: str) -> date:
    """Parse date from dd/mm/yyyy string."""
    m = re.search(r"(\d{2})/(\d{2})/(\d{4})", date_str)
    if not m:
        raise ValueError(f"Invalid date format: {date_str}")
    return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))


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

    @property
    def survey_date(self) -> date | None:
        """The last day of the price survey (fim do levantamento), per RN07."""
        if not self.survey_end:
            return None
        return parse_date_br(self.survey_end)


RIGHT_COL_KEYS = [
    "Data:",
    "Modalidade:",
    "SRP:",
    "Identificação:",
    "Lote/Item:",
    "Ata:",
    "Homologação:",
    "Quantidade:",
    "Unidade:",
    "UF:",
]

RIGHT_RE = re.compile(r"\s+(" + "|".join(re.escape(k) for k in RIGHT_COL_KEYS) + r")\s*(.*)$")
LEFT_COL_KEYS = ["CNPJ:", "Órgão:", "Objeto:", "Descrição:", "Fonte:"]

PRICE_HEADER_RE = re.compile(
    r"^[ \t]*Preço\s*\((?P<category>[^)]+)\)\s*(?P<num>\d+):\s*"
    r"(?P<method>.+?)\s+R\$\s*(?P<price>[0-9.,]+)",
    re.MULTILINE,
)

ITEM_HEADER_RE = re.compile(r"^[ \t]*Item\s+(\d+):\s*([^\n]+)", re.MULTILINE)


def extract_pdf_layout_text(pdf_path: Path) -> str:
    """Extract text from PDF preserving layout using pdftotext -layout."""
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file does not exist: {pdf_path}")
    res = subprocess.run(
        ["pdftotext", "-layout", str(pdf_path), "-"],
        capture_output=True,
        text=True,
        check=True,
    )
    return res.stdout


def _parse_decimal_br(val_str: str) -> Decimal:
    cleaned = val_str.strip()
    if "," in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    return Decimal(cleaned)


def _parse_pncp_key(
    source_url: str,
    identifier: str | None,
    lote_item: str | None,
) -> dict[str, Any] | None:
    if not source_url or "pncp.gov.br" not in source_url.lower():
        return None

    cnpj: str | None = None
    ano: int | None = None
    sequencial: int | None = None

    m_url = re.search(r"/editais/(\d{14})/(\d{4})/(\d+)", source_url)
    if m_url:
        cnpj = m_url.group(1)
        ano = int(m_url.group(2))
        sequencial = int(m_url.group(3))
    elif identifier:
        m_id = re.search(r"(\d{14})-1-(\d+)/(\d{4})", identifier)
        if m_id:
            cnpj = m_id.group(1)
            sequencial = int(m_id.group(2))
            ano = int(m_id.group(3))

    if not cnpj or ano is None or sequencial is None:
        return None

    numero_item = None
    if lote_item:
        parts = lote_item.split("/")
        candidate = parts[-1].strip()
        if candidate.isdigit():
            numero_item = int(candidate)

    if numero_item is None:
        return None

    return {
        "cnpj": cnpj,
        "ano": ano,
        "sequencial": sequencial,
        "numero_item": numero_item,
    }


def _parse_price_block(
    block: str,
    category: str,
    method: str,
    price_str: str,
    num: int,
) -> ChosenPriceReport:
    left_fields: dict[str, str] = {}
    right_fields: dict[str, str] = {}
    current_left_key: str | None = None

    supplier_pos = block.find("Razão Social do Fornecedor")
    header_part = block[:supplier_pos] if supplier_pos != -1 else block

    for line in header_part.splitlines():
        if not line.strip() or "Art. 5º da IN 65" in line:
            continue
        m_r = RIGHT_RE.search(line)
        if m_r:
            left_chunk = line[: m_r.start()].strip()
            r_key = m_r.group(1).rstrip(":")
            r_val = m_r.group(2).strip()
            right_fields[r_key] = r_val
        else:
            left_chunk = line.strip()

        if left_chunk:
            matched_lkey = None
            for lk in LEFT_COL_KEYS:
                if left_chunk.startswith(lk):
                    matched_lkey = lk
                    break
            if matched_lkey:
                current_left_key = matched_lkey.rstrip(":")
                val = left_chunk[len(matched_lkey) :].strip()
                left_fields[current_left_key] = val
            elif current_left_key:
                left_fields[current_left_key] += " " + left_chunk

    raw_source = left_fields.get("Fonte", "").strip()
    source = raw_source.split()[0] if raw_source else ""
    identifier = right_fields.get("Identificação")
    lote_item = right_fields.get("Lote/Item")
    pncp_key = _parse_pncp_key(source, identifier, lote_item)

    agency = left_fields.get("Órgão", "").strip()
    price_date = right_fields.get("Data", "").strip()
    try:
        unit_price = _parse_decimal_br(price_str)
    except Exception as exc:
        raise ParseError(f"Price {num} has invalid price string: {price_str}") from exc

    if not agency:
        raise ParseError(f"Price {num} is missing agency (Órgão)")
    if not price_date:
        raise ParseError(f"Price {num} is missing date (Data)")
    if unit_price <= 0:
        raise ParseError(f"Price {num} has non-positive price: {unit_price}")

    return ChosenPriceReport(
        price_number=num,
        source_category=category.strip(),
        calculation_method=method.strip(),
        unit_price=unit_price,
        agency=agency,
        date=price_date,
        chosen_description=left_fields.get("Descrição", "").strip(),
        source=source,
        identifier=identifier,
        item_number_raw=lote_item,
        pncp_key=pncp_key,
        state=right_fields.get("UF"),
        modality=right_fields.get("Modalidade"),
        unit=right_fields.get("Unidade"),
        quantity=right_fields.get("Quantidade"),
    )


def parse_quotation_report_text(text: str, report_id: str = "") -> QuotationReport:
    """Parse quotation report text into QuotationReport dataclass."""
    norm_text = text.replace("\x0c", "\n")

    m_title = re.search(r"Relatório de Cotação:\s*([^\n]+)", norm_text)
    title = m_title.group(1).strip() if m_title else ""

    m_survey = re.search(r"Pesquisa realizada entre\s*([0-9/ :]+)\s*e\s*([0-9/ :]+)", norm_text)
    if not m_survey:
        raise ParseError("Quotation report is missing 'Pesquisa realizada entre' section")
    survey_start = m_survey.group(1).strip()
    survey_end = m_survey.group(2).strip()

    m_gen = re.search(r"Relatório gerado no dia\s*([0-9/ :]+)", norm_text)
    generated_at = m_gen.group(1).strip() if m_gen else None

    # Validate item headers count and uniqueness
    raw_item_headers = re.findall(r"^[ \t]*Item\s+(\d+):", norm_text, re.MULTILINE)
    item_matches = list(ITEM_HEADER_RE.finditer(norm_text))
    if len(raw_item_headers) != len(item_matches):
        raise ParseError(
            f"Item count mismatch: {len(raw_item_headers)} headers, extracted {len(item_matches)}"
        )
    item_numbers = [int(m.group(1)) for m in item_matches]
    if len(set(item_numbers)) != len(item_numbers):
        raise ParseError(f"Item count mismatch or duplicate item numbers found: {item_numbers}")

    items: list[RequestedItemReport] = []

    for idx, im in enumerate(item_matches):
        item_num = int(im.group(1))
        short_desc = im.group(2).strip()
        start = im.end()
        end = item_matches[idx + 1].start() if idx + 1 < len(item_matches) else len(norm_text)
        item_section = norm_text[start:end]

        m_extrato = re.search(r"Extrato de fontes", item_section)
        if m_extrato:
            item_section = item_section[: m_extrato.start()]

        fp = PRICE_HEADER_RE.search(item_section)
        item_header_text = item_section[: fp.start()] if fp else item_section

        m_calc = re.search(r"Preço Estimado Calculado:\s*R\$\s*([0-9.,]+)", item_header_text)
        m_est = re.search(r"Preço Estimado:\s*R\$\s*([0-9.,]+)", item_header_text)
        if m_calc:
            est_price = _parse_decimal_br(m_calc.group(1))
        elif m_est:
            est_price = _parse_decimal_br(m_est.group(1))
        else:
            raise ParseError(f"Item {item_num} is missing estimated price (Preço Estimado)")

        # Estimation method name (e.g. Média dos Preços Obtidos or Mediana dos Preços Obtidos)
        m_method = re.search(
            r"((?:Média|Mediana|Menor Preço|Menor valor)[^\n:]*):\s*R\$",
            item_header_text,
            re.IGNORECASE,
        )
        estimation_method = m_method.group(1).strip() if m_method else "Média dos Preços Obtidos"

        # Quantity and unit
        q_match = re.search(
            r"Quantidade\s+Descrição.*?\n(.*?)(?=\n\s*(?:Preço|Relatório|$))",
            item_header_text,
            re.DOTALL,
        )
        if not q_match:
            raise ParseError(f"Item {item_num} is missing unit or quantity block")

        raw_lines = [line.strip() for line in q_match.group(1).splitlines() if line.strip()]
        if not raw_lines:
            raise ParseError(f"Item {item_num} has empty quantity/description section")

        first_line = raw_lines[0]
        parts = re.split(r"\s{2,}", first_line, maxsplit=1)
        if len(parts) < 2:
            msg = (
                f"Item {item_num} missing unit or quantity or "
                f"not separated by column boundary: '{first_line}'"
            )
            raise ParseError(msg)
        first_col = parts[0].strip()
        desc_first = parts[1].strip()
        qm = re.match(r"^([0-9.,]+)\s+(.+)$", first_col)
        if not qm:
            raise ParseError(f"Item {item_num} missing unit or quantity in: '{first_col}'")

        quantity = _parse_decimal_br(qm.group(1))
        unit = qm.group(2).strip()
        if not unit or quantity <= 0:
            raise ParseError(
                f"Item {item_num} has invalid unit or quantity: unit='{unit}', qty='{quantity}'"
            )

        desc_parts = [desc_first] if desc_first else []
        desc_parts.extend(raw_lines[1:])
        full_desc = " ".join(desc_parts).strip()

        # Parse chosen prices
        price_matches = list(PRICE_HEADER_RE.finditer(item_section))
        raw_price_headers = re.findall(r"^[ \t]*Preço\s*\(", item_section, re.MULTILINE)
        if len(raw_price_headers) != len(price_matches):
            raise ParseError(
                f"Price header count mismatch in item {item_num}: "
                f"found {len(raw_price_headers)} headers, extracted {len(price_matches)} prices"
            )

        chosen_prices: list[ChosenPriceReport] = []

        for p_idx, pm in enumerate(price_matches):
            p_start = pm.end()
            p_end = (
                price_matches[p_idx + 1].start()
                if p_idx + 1 < len(price_matches)
                else len(item_section)
            )
            p_block = item_section[p_start:p_end]
            m_next_it = ITEM_HEADER_RE.search(p_block)
            if m_next_it:
                p_block = p_block[: m_next_it.start()]

            price_report = _parse_price_block(
                block=p_block,
                category=pm.group("category"),
                method=pm.group("method"),
                price_str=pm.group("price"),
                num=int(pm.group("num")),
            )
            chosen_prices.append(price_report)

        items.append(
            RequestedItemReport(
                item_number=item_num,
                short_description=short_desc,
                description=full_desc if full_desc else short_desc,
                unit=unit,
                quantity=quantity,
                estimated_unit_price=est_price,
                estimation_method=estimation_method,
                chosen_prices=tuple(chosen_prices),
            )
        )

    # Global check on total prices extracted
    total_raw_prices = len(re.findall(r"^[ \t]*Preço\s*\(", norm_text, re.MULTILINE))
    total_extracted_prices = sum(len(it.chosen_prices) for it in items)
    if total_raw_prices != total_extracted_prices:
        raise ParseError(
            f"Price header count mismatch across report: "
            f"found {total_raw_prices} headers, extracted {total_extracted_prices} prices"
        )

    return QuotationReport(
        report_id=report_id,
        title=title,
        survey_start=survey_start,
        survey_end=survey_end,
        generated_at=generated_at,
        items=tuple(items),
    )
