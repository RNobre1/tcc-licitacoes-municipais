from ingestion.item_kind import map_item_kind


def test_map_item_kind_service_for_s():
    assert map_item_kind("S") == "service"
    assert map_item_kind("s") == "service"
    assert map_item_kind(" S ") == "service"


def test_map_item_kind_product_for_anything_else():
    assert map_item_kind("M") == "product"
    assert map_item_kind("m") == "product"
    assert map_item_kind("P") == "product"
    assert map_item_kind("") == "product"
    assert map_item_kind("   ") == "product"
    assert map_item_kind(None) == "product"
    assert map_item_kind("other") == "product"
