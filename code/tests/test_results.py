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
