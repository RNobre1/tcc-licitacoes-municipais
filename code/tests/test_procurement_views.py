from html import escape

from django.urls import reverse

from procurement import demo_data


def test_procurement_list_view_returns_200_and_provides_procurements_in_context(
    client,
):
    url = reverse("procurement:list")
    response = client.get(url)

    assert response.status_code == 200
    assert response.context["procurements"] == demo_data.list_procurements()


def test_procurement_detail_view_returns_200_and_provides_procurement_in_context(client):
    url = reverse("procurement:detail", args=[1])
    response = client.get(url)

    assert response.status_code == 200
    assert response.context["procurement"] == demo_data.get_procurement(1)


def test_procurement_detail_view_returns_404_for_invalid_procurement_id(client):
    url = reverse("procurement:detail", args=[999])
    response = client.get(url)

    assert response.status_code == 404


def test_procurement_list_is_served_at_the_contract_path(client):
    assert reverse("procurement:list") == "/procurements/"
    assert client.get("/procurements/").status_code == 200


def test_procurement_list_renders_its_template_with_every_procurement_linked_to_its_detail(client):
    response = client.get("/procurements/")
    html = response.content.decode()

    assert "procurement/procurement_list.html" in [t.name for t in response.templates]
    assert len(demo_data.list_procurements()) >= 1
    for procurement in demo_data.list_procurements():
        assert f'href="/procurements/{procurement.id}/"' in html
        assert escape(procurement.title) in html
