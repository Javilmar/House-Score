"""T024 - POST /ingest con secreto correcto."""

from tests.conftest import AUTH
from tests.factories import listing, pasada


def test_ingest_devuelve_201_y_resumen(client):
    r = client.post(
        "/ingest", json=pasada(listing(), listing(url="https://ejemplo/2")), headers=AUTH
    )
    assert r.status_code == 201
    assert r.json() == {
        "listings_procesados": 2,
        "nuevos": 2,
        "actualizados": 0,
        "descartados_bloqueados": 0,
        "retirados": 0,
    }


def test_el_listing_queda_disponible_inmediatamente(client):
    client.post("/ingest", json=pasada(listing()), headers=AUTH)
    assert [x["url"] for x in client.get("/listings").json()] == ["https://ejemplo/piso-1"]


def test_cuerpo_invalido_devuelve_422(client):
    r = client.post("/ingest", json={"listings": [{"titulo": "sin url"}]}, headers=AUTH)
    assert r.status_code == 422
