from datetime import date, datetime

from ingestion.metrics import (
    distinct_units,
    median_description_length,
    missing_share,
    volume_per_day,
)


class TestVolumePerDay:
    def test_empty_input(self):
        assert volume_per_day([]) == {}

    def test_counts_publications_by_date(self):
        publications = [
            {"dataPublicacaoPncp": "2025-08-01"},
            {"dataPublicacaoPncp": "2025-08-01"},
            {"dataPublicacaoPncp": "2025-08-02"},
        ]
        assert volume_per_day(publications) == {
            date(2025, 8, 1): 2,
            date(2025, 8, 2): 1,
        }

    def test_data_publicacao_pncp_with_time_part(self):
        publications = [
            {"dataPublicacaoPncp": "2025-08-01T10:30:00"},
            {"dataPublicacaoPncp": "2025-08-01T23:59:59Z"},
            {"dataPublicacaoPncp": "2025-08-01 14:00:00"},
            {"dataPublicacaoPncp": "2025-08-02T00:00:00-03:00"},
        ]
        assert volume_per_day(publications) == {
            date(2025, 8, 1): 3,
            date(2025, 8, 2): 1,
        }

    def test_data_publicacao_pncp_date_and_datetime_objects(self):
        publications = [
            {"dataPublicacaoPncp": date(2025, 8, 1)},
            {"dataPublicacaoPncp": datetime(2025, 8, 1, 15, 30)},
        ]
        assert volume_per_day(publications) == {
            date(2025, 8, 1): 2,
        }

    def test_none_or_missing_date_ignored(self):
        publications = [
            {"dataPublicacaoPncp": "2025-08-01"},
            {"dataPublicacaoPncp": None},
            {"other_field": "val"},
        ]
        assert volume_per_day(publications) == {
            date(2025, 8, 1): 1,
        }

    def test_generator_input(self):
        publications = ({"dataPublicacaoPncp": f"2025-08-0{i}"} for i in (1, 1, 2))
        assert volume_per_day(publications) == {
            date(2025, 8, 1): 2,
            date(2025, 8, 2): 1,
        }


class TestMissingShare:
    def test_empty_input(self):
        assert missing_share([], "descricao") is None

    def test_field_missing_in_every_record(self):
        items = [
            {"unidadeMedida": "KG"},
            {"unidadeMedida": "UN"},
            {"unidadeMedida": "LT"},
        ]
        assert missing_share(items, "descricao") == 1.0

    def test_field_present_in_every_record(self):
        items = [
            {"descricao": "Item 1"},
            {"descricao": "Item 2"},
        ]
        assert missing_share(items, "descricao") == 0.0

    def test_partial_missing_share(self):
        items = [
            {"descricao": "Item 1"},
            {"descricao": "Item 2"},
            {"descricao": None},
            {"other": "value"},
        ]
        assert missing_share(items, "descricao") == 0.5

    def test_none_value_counts_as_missing(self):
        items = [
            {"field": None},
            {"field": "valid"},
        ]
        assert missing_share(items, "field") == 0.5

    def test_empty_or_blank_strings_count_as_missing(self):
        items = [
            {"field": ""},
            {"field": "   "},
            {"field": "\t\n"},
            {"field": "valid"},
        ]
        assert missing_share(items, "field") == 0.75

    def test_zero_and_false_are_not_missing(self):
        items = [
            {"valor": 0},
            {"valor": 0.0},
            {"ativo": False},
        ]
        assert missing_share(items, "valor") == 0.3333333333333333  # only 3rd record lacks 'valor'
        assert missing_share(items[:2], "valor") == 0.0
        assert missing_share(items[2:], "ativo") == 0.0

    def test_generator_input(self):
        items = ({"field": "ok"} if i % 2 == 0 else {"field": None} for i in range(4))
        assert missing_share(items, "field") == 0.5


class TestMedianDescriptionLength:
    def test_empty_input(self):
        assert median_description_length([]) is None

    def test_all_descriptions_missing_returns_none(self):
        items = [
            {"descricao": None},
            {"descricao": ""},
            {"descricao": "   "},
            {"other": 123},
        ]
        assert median_description_length(items) is None

    def test_odd_number_of_descriptions(self):
        items = [
            {"descricao": "12345"},  # 5
            {"descricao": "1234567890"},  # 10
            {"descricao": "123456789012345"},  # 15
        ]
        assert median_description_length(items) == 10.0

    def test_even_number_of_descriptions(self):
        items = [
            {"descricao": "1234567890"},  # 10
            {"descricao": "12345678901234567890"},  # 20
        ]
        assert median_description_length(items) == 15.0

    def test_returns_float_type(self):
        items = [{"descricao": "item"}]
        result = median_description_length(items)
        assert isinstance(result, float)
        assert result == 4.0

    def test_missing_descriptions_are_not_counted_as_zero(self):
        # If missing was counted as zero, median of [0, 10] would be 5.0.
        # But missing descriptions are ignored, so median of [10] is 10.0.
        items = [
            {"descricao": "1234567890"},
            {"descricao": None},
            {"descricao": ""},
            {"descricao": "   "},
            {},
        ]
        assert median_description_length(items) == 10.0

    def test_strip_whitespace_before_measuring_length(self):
        items = [
            {"descricao": "  papel a4  "},  # "papel a4" has length 8
        ]
        assert median_description_length(items) == 8.0

    def test_generator_input(self):
        items = ({"descricao": "a" * (i * 2)} for i in (1, 2, 3))
        assert median_description_length(items) == 4.0


class TestDistinctUnits:
    def test_empty_input(self):
        assert distinct_units([]) == 0

    def test_counts_distinct_units(self):
        items = [
            {"unidadeMedida": "KG"},
            {"unidadeMedida": "LITRO"},
            {"unidadeMedida": "UNIDADE"},
        ]
        assert distinct_units(items) == 3

    def test_case_and_space_differences_are_normalized(self):
        items = [
            {"unidadeMedida": "UNIDADE"},
            {"unidadeMedida": "unidade"},
            {"unidadeMedida": "  Unidade  "},
            {"unidadeMedida": "unidade "},
            {"unidadeMedida": "KG"},
            {"unidadeMedida": " kg "},
        ]
        assert distinct_units(items) == 2

    def test_missing_and_none_units_ignored(self):
        items = [
            {"unidadeMedida": "UN"},
            {"unidadeMedida": None},
            {"unidadeMedida": ""},
            {"unidadeMedida": "   "},
            {"other_field": "val"},
        ]
        assert distinct_units(items) == 1

    def test_all_missing_returns_zero(self):
        items = [
            {"unidadeMedida": None},
            {"unidadeMedida": ""},
            {"unidadeMedida": "   "},
            {},
        ]
        assert distinct_units(items) == 0

    def test_generator_input(self):
        items = ({"unidadeMedida": u} for u in ("caixa", "CAIXA", "  caixa  ", "pacote"))
        assert distinct_units(items) == 2
