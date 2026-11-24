"""Parser for QuotationReport documents."""

import re
import subprocess
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

RIGHT_RE = re.compile(r"\s{2,}(" + "|".join(re.escape(k) for k in RIGHT_COL_KEYS) + r")\s*(.*)$")
LEFT_COL_KEYS = ["CNPJ:", "Órgão:", "Objeto:", "Descrição:", "Fonte:"]

PRICE_HEADER_RE = re.compile(
    r"^[ \t]*Preço\s*\((?P<category>[^)]+)\)\s*(?P<num>\d+):\s*"
    r"(?P<method>[^R\n]+?)\s*R\$\s*(?P<price>[0-9.,]+)",
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
    cleaned = val_str.strip().replace(".", "").replace(",", ".")
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

    return ChosenPriceReport(
        price_number=num,
        source_category=category.strip(),
        calculation_method=method.strip(),
        unit_price=_parse_decimal_br(price_str),
        agency=left_fields.get("Órgão", "").strip(),
        date=right_fields.get("Data", "").strip(),
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
    survey_start = m_survey.group(1).strip() if m_survey else None
    survey_end = m_survey.group(2).strip() if m_survey else None

    m_gen = re.search(r"Relatório gerado no dia\s*([0-9/ :]+)", norm_text)
    generated_at = m_gen.group(1).strip() if m_gen else None

    item_matches = list(ITEM_HEADER_RE.finditer(norm_text))
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
            est_price = Decimal("0.00")

        # Estimation method name (e.g. Média dos Preços Obtidos or Mediana dos Preços Obtidos)
        m_method = re.search(
            r"((?:Média|Mediana|Menor Preço|Menor valor)[^\n:]*):\s*R\$",
            item_header_text,
            re.IGNORECASE,
        )
        estimation_method = m_method.group(1).strip() if m_method else "Média dos Preços Obtidos"

        # Quantity and unit
        quantity = Decimal("1")
        unit = "Unidade"
        full_desc = short_desc

        q_match = re.search(
            r"Quantidade\s+Descrição.*?\n(.*?)(?=\n\s*(?:Preço|Relatório|$))",
            item_header_text,
            re.DOTALL,
        )
        if q_match:
            raw_lines = [line.strip() for line in q_match.group(1).splitlines() if line.strip()]
            if raw_lines:
                first_line = raw_lines[0]
                qm = re.match(
                    r"^\s*([0-9.,]+)\s+([A-Za-zÀ-ÿ.]+(?:\s+[A-Za-zÀ-ÿ.]+)?)\s+(.*)",
                    first_line,
                )
                if qm:
                    quantity = _parse_decimal_br(qm.group(1))
                    unit = qm.group(2).strip()
                    desc_parts = [qm.group(3).strip()] if qm.group(3).strip() else []
                    desc_parts.extend(raw_lines[1:])
                    full_desc = " ".join(desc_parts).strip()
                else:
                    full_desc = " ".join(raw_lines).strip()

        # Parse chosen prices
        price_matches = list(PRICE_HEADER_RE.finditer(item_section))
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

    return QuotationReport(
        report_id=report_id,
        title=title,
        survey_start=survey_start,
        survey_end=survey_end,
        generated_at=generated_at,
        items=tuple(items),
    )
