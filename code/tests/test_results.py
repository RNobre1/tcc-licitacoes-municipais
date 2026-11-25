import pytest

from ingestion.results import select_valid_result


def test_select_valid_result_picks_informado_without_cancellation():
    results = [
        {
            "numeroItem": 1,
            "situacaoCompraItemResultadoNome": "Informado",
            "dataCancelamento": None,
            "valorUnitarioHomologado": 42.50,
            "nomeRazaoSocialFornecedor": "Empresa Vencedora LTDA",
        }
    ]
    selected = select_valid_result(results)
    assert selected is not None
    assert selected["situacaoCompraItemResultadoNome"] == "Informado"
    assert selected["valorUnitarioHomologado"] == 42.50
    assert selected["nomeRazaoSocialFornecedor"] == "Empresa Vencedora LTDA"


def test_select_valid_result_ignores_cancelled_or_non_informado():
    results = [
        {
            "numeroItem": 1,
            "situacaoCompraItemResultadoNome": "Informado",
            "dataCancelamento": "2026-11-20T10:00:00",
            "valorUnitarioHomologado": 10.0,
        },
        {
            "numeroItem": 1,
            "situacaoCompraItemResultadoNome": "Cancelado",
            "dataCancelamento": None,
            "valorUnitarioHomologado": 20.0,
        },
        {
            "numeroItem": 1,
            "situacaoCompraItemResultadoNome": "Revogado",
            "dataCancelamento": None,
            "valorUnitarioHomologado": 30.0,
        },
    ]
    assert select_valid_result(results) is None


def test_select_valid_result_picks_first_valid_when_multiple():
    results = [
        {
            "numeroItem": 1,
            "situacaoCompraItemResultadoNome": "Informado",
            "dataCancelamento": "2026-11-20T10:00:00",
            "valorUnitarioHomologado": 10.0,
        },
        {
            "numeroItem": 1,
            "situacaoCompraItemResultadoNome": "Informado",
            "dataCancelamento": None,
            "valorUnitarioHomologado": 15.0,
            "id": 1,
        },
        {
            "numeroItem": 1,
            "situacaoCompraItemResultadoNome": "Informado",
            "dataCancelamento": None,
            "valorUnitarioHomologado": 20.0,
            "id": 2,
        },
    ]
    selected = select_valid_result(results)
    assert selected is not None
    assert selected["id"] == 1
    assert selected["valorUnitarioHomologado"] == 15.0


def test_select_valid_result_handles_empty_or_invalid_inputs():
    assert select_valid_result([]) is None
    assert select_valid_result(None) is None
    assert select_valid_result({}) is None
    assert select_valid_result(["not-a-dict"]) is None


@pytest.mark.parametrize(
    "unreadable_or_nonpositive_price",
    [None, "not-a-price", 0, 0.0, -1, "-2.5", "NaN", "Infinity", [], {}],
)
def test_select_valid_result_skips_informed_results_without_usable_price(
    unreadable_or_nonpositive_price,
):
    first_result = {
        "situacaoCompraItemResultadoNome": "Informado",
        "dataCancelamento": None,
        "valorUnitarioHomologado": unreadable_or_nonpositive_price,
        "id": "missing-or-invalid-price",
    }
    later_result = {
        "situacaoCompraItemResultadoNome": "Informado",
        "dataCancelamento": None,
        "valorUnitarioHomologado": "10.50",
        "id": "priced-result",
    }

    assert select_valid_result([first_result, later_result]) is later_result


def test_select_valid_result_returns_none_when_no_informed_result_has_usable_price():
    results = [
        {
            "situacaoCompraItemResultadoNome": "Informado",
            "dataCancelamento": None,
        },
        {
            "situacaoCompraItemResultadoNome": "Informado",
            "dataCancelamento": None,
            "valorUnitarioHomologado": 0,
        },
        {
            "situacaoCompraItemResultadoNome": "Informado",
            "dataCancelamento": None,
            "valorUnitarioHomologado": "invalid",
        },
    ]

    assert select_valid_result(results) is None
