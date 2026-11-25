import pytest

from ingestion.item_kind import map_item_kind


@pytest.mark.parametrize(
    ("code", "name", "expected"),
    [
        ("S", "Material", "service"),
        ("s", None, "service"),
        (" s ", None, "product"),
        ("M", None, "product"),
        ("N", None, "product"),
        ("X", None, "product"),
        ("M", "Serviço", "service"),
        ("M", "Serviços e obras", "service"),
        ("N", "Serviço", "service"),
        ("X", "Material de serviço", "service"),
        (None, "Prestação de serviço", "service"),
        (None, "Serviço", "service"),
        (None, "Material", "product"),
        ("", "Material", "product"),
        (None, None, "product"),
        ("P", "Produto", "product"),
        ("S", "", "service"),
        (17, None, "product"),
    ],
    ids=[
        "service-code-overrides-name",
        "lowercase-service-code",
        "spaces-around-code-remain-product",
        "material-code-without-name",
        "unknown-code-without-name",
        "other-code-without-name",
        "material-code-service-name",
        "material-code-services-and-works-name",
        "unknown-code-service-name",
        "material-service-name",
        "service-in-name-suffix",
        "service-name-without-code",
        "material-name-without-code",
        "empty-code-material-name",
        "empty-inputs",
        "product-code-and-name",
        "service-code-empty-name",
        "numeric-code",
    ],
)
def test_map_item_kind_matches_the_approved_builder_rule(code, name, expected):
    assert map_item_kind(code, name) == expected
