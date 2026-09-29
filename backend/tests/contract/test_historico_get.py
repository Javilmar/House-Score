"""T018 - contrato de GET /historico."""

from datetime import date

from tests.conftest import AUTH
from tests.factories import listing, pasada


def test_shape_y_agregados_por_dia(client, hoy):
    hoy["fecha"] = date(2026, 9, 28)
    client.post(
        "/ingest",
        json=pasada(
            listing(url="https://e/1", precio=100000, score=40.0),
            listing(url="https://e/2", precio=200000, score=60.0),
            listing(url="https://e/3", precio=300000, m2=None, score=None),
        ),
        headers=AUTH,
    )
    hoy["fecha"] = date(2026, 9, 29)
    client.post("/ingest", json=pasada(listing(url="https://e/1", precio=100000)), headers=AUTH)

    r = client.get("/historico")
    assert r.status_code == 200
    filas = r.json()
    assert [f["fecha"] for f in filas] == ["2026-09-28", "2026-09-29"]
    dia1 = filas[0]
    assert set(dia1) >= {"fecha", "total_listings", "score_medio", "precio_medio"}
    assert dia1["total_listings"] == 3
    assert dia1["score_medio"] == 50.0  # excluye el listing sin datos suficientes
    assert dia1["precio_medio"] == 200000


def test_filtra_por_rango_de_fechas(client, hoy):
    for d in (date(2026, 9, 1), date(2026, 9, 10), date(2026, 9, 20)):
        hoy["fecha"] = d
        client.post("/ingest", json=pasada(listing()), headers=AUTH)
    r = client.get("/historico", params={"desde": "2026-09-05", "hasta": "2026-09-15"})
    assert [f["fecha"] for f in r.json()] == ["2026-09-10"]
