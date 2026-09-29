"""T028 - FR-006: municipios bloqueados de Toledo Norte se descartan antes de persistir."""

import pytest

from tests.conftest import AUTH
from tests.factories import listing, pasada


@pytest.mark.parametrize(
    "muni",
    ["yuncos", "Yuncos", "cabanas_de_la_sagra", "Cabañas de la Sagra", "el viso de san juan"],
)
def test_bloqueado_no_se_persiste(client, muni):
    r = client.post(
        "/ingest",
        json=pasada(listing(url="https://e/ok"), listing(url="https://e/bloq", municipio=muni)),
        headers=AUTH,
    )
    assert r.json()["descartados_bloqueados"] == 1
    assert r.json()["listings_procesados"] == 1
    body = client.get("/listings", params={"incluir_retirados": True}).json()
    assert [b["url"] for b in body] == ["https://e/ok"]


def test_municipio_permitido_pasa(client):
    r = client.post("/ingest", json=pasada(listing(municipio="illescas")), headers=AUTH)
    assert r.json()["descartados_bloqueados"] == 0
