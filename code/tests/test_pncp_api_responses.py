import json
from pathlib import Path

PNCP_RESPONSES_DIR = Path(__file__).parent / "api_responses" / "pncp"


def _read_json(filename: str):
    return json.loads((PNCP_RESPONSES_DIR / filename).read_text(encoding="utf-8"))


def test_pncp_response_files_exist():
    assert PNCP_RESPONSES_DIR.is_dir()
    expected_files = [
        "publications_page_1.json",
        "publications_page_2.json",
        "items_page_1.json",
        "items_page_2.json",
        "items_quantity.json",
        "README.md",
    ]
    for filename in expected_files:
        filepath = PNCP_RESPONSES_DIR / filename
        assert filepath.is_file(), f"Expected file {filename} does not exist"


def test_publications_envelope_and_pagination():
    page_1_path = PNCP_RESPONSES_DIR / "publications_page_1.json"
    page_2_path = PNCP_RESPONSES_DIR / "publications_page_2.json"

    assert page_1_path.is_file()
    assert page_2_path.is_file()

    page_1 = json.loads(page_1_path.read_text(encoding="utf-8"))
    page_2 = json.loads(page_2_path.read_text(encoding="utf-8"))

    for page in (page_1, page_2):
        for field in (
            "data",
            "totalRegistros",
            "totalPaginas",
            "numeroPagina",
            "paginasRestantes",
        ):
            assert field in page
        assert isinstance(page["data"], list)
        assert page["totalPaginas"] == 2

    assert page_1["numeroPagina"] == 1
    assert page_1["paginasRestantes"] == 1

    assert page_2["numeroPagina"] == 2
    assert page_2["paginasRestantes"] == 0

    total_records = len(page_1["data"]) + len(page_2["data"])
    assert page_1["totalRegistros"] == total_records
    assert page_2["totalRegistros"] == total_records


def test_publications_documented_fields_and_fictitious_content():
    page_1 = _read_json("publications_page_1.json")
    page_2 = _read_json("publications_page_2.json")

    publications = page_1["data"] + page_2["data"]
    assert len(publications) >= 2

    dates = set()
    for pub in publications:
        assert isinstance(pub["orgaoEntidade"], dict)
        cnpj = pub["orgaoEntidade"]["cnpj"]
        assert isinstance(cnpj, str)
        assert set(cnpj.replace(".", "").replace("/", "").replace("-", "")).issubset({"0", "9"})

        razao_social = pub["orgaoEntidade"]["razaoSocial"]
        assert "Prefeitura Fictícia" in razao_social

        assert isinstance(pub["anoCompra"], int)
        assert isinstance(pub["sequencialCompra"], int)
        assert isinstance(pub["numeroControlePNCP"], str)

        objeto = pub["objetoCompra"]
        assert isinstance(objeto, str)
        assert objeto.startswith("DEMO-")

        data_pub = pub["dataPublicacaoPncp"]
        assert isinstance(data_pub, str)
        dates.add(data_pub[:10])

        assert pub["modalidadeId"] == 6

        assert isinstance(pub["unidadeOrgao"], dict)
        assert pub["unidadeOrgao"]["ufSigla"] == "PA"

        assert isinstance(pub["valorTotalEstimado"], (int, float))

    assert len(dates) >= 2


def test_items_bare_arrays_and_documented_fields():
    page_1_path = PNCP_RESPONSES_DIR / "items_page_1.json"
    page_2_path = PNCP_RESPONSES_DIR / "items_page_2.json"

    assert page_1_path.is_file()
    assert page_2_path.is_file()

    items_1 = json.loads(page_1_path.read_text(encoding="utf-8"))
    items_2 = json.loads(page_2_path.read_text(encoding="utf-8"))

    assert isinstance(items_1, list)
    assert isinstance(items_2, list)

    all_items = items_1 + items_2
    assert len(all_items) >= 2

    for item in all_items:
        assert isinstance(item["numeroItem"], int)
        assert isinstance(item["descricao"], str)
        assert isinstance(item["quantidade"], (int, float))
        assert isinstance(item["valorUnitarioEstimado"], (int, float))
        assert isinstance(item["criterioJulgamentoNome"], str)
        assert isinstance(item["temResultado"], bool)
        assert isinstance(item["orcamentoSigiloso"], bool)


def test_items_metrics_edge_cases():
    items_1 = _read_json("items_page_1.json")
    items_2 = _read_json("items_page_2.json")
    all_items = items_1 + items_2

    # Edge case 1: one item with empty descricao
    empty_desc_items = [item for item in all_items if item["descricao"].strip() == ""]
    assert len(empty_desc_items) == 1

    # Non-empty descriptions use DEMO- prefix
    for item in all_items:
        if item["descricao"].strip():
            assert item["descricao"].startswith("DEMO-")

    # Edge case 2: one item without unidadeMedida (missing key or None)
    without_unit = [
        item for item in all_items if "unidadeMedida" not in item or item["unidadeMedida"] is None
    ]
    assert len(without_unit) == 1

    # Edge case 3: two unit spellings differing only in case or spaces
    units = [
        item["unidadeMedida"]
        for item in all_items
        if "unidadeMedida" in item and item["unidadeMedida"] is not None
    ]
    matching_pairs = [
        (u1, u2)
        for i, u1 in enumerate(units)
        for u2 in units[i + 1 :]
        if u1 != u2 and u1.strip().casefold() == u2.strip().casefold()
    ]
    assert len(matching_pairs) >= 1


def test_items_count_equals_quantity():
    items_1 = _read_json("items_page_1.json")
    items_2 = _read_json("items_page_2.json")
    quantity_text = (PNCP_RESPONSES_DIR / "items_quantity.json").read_text(encoding="utf-8").strip()

    quantity = json.loads(quantity_text)
    assert isinstance(quantity, int)
    assert len(items_1) + len(items_2) == quantity


def test_readme_documents_synthetic_data_and_endpoints():
    readme_path = PNCP_RESPONSES_DIR / "README.md"
    assert readme_path.is_file()
    content = readme_path.read_text(encoding="utf-8")

    assert "synthetic" in content.lower()
    assert "/api/consulta/v1/contratacoes/publicacao" in content
    assert "/api/pncp/v1/orgaos/{cnpj}/compras/{ano}/{sequencial}/itens" in content
    assert "itens/quantidade" in content
