"""T017 - contrato de GET /listings."""

from datetime import date

from tests.conftest import AUTH
from tests.factories import listing, pasada


def sembrar(client, *items):
    r = client.post("/ingest", json=pasada(*items), headers=AUTH)
    assert r.status_code == 201, r.text


def test_cada_listing_trae_score_y_datos_insuficientes(client):
    sembrar(client, listing(), listing(url="https://ejemplo/2", m2=None, score=None))
    r = client.get("/listings")
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 2
    for it in body:
        for campo in (
            "url",
            "titulo",
            "precio",
            "m2",
            "habitaciones",
            "banos",
            "municipio",
            "fuente",
            "score",
            "datos_insuficientes",
            "estado",
            "primera_aparicion",
            "ultima_aparicion",
        ):
            assert campo in it, campo


def test_sin_m2_se_sirve_sin_score_forzado(client):
    sembrar(client, listing(m2=None, score=77.0))
    (it,) = client.get("/listings").json()
    assert it["datos_insuficientes"] is True
    assert it["score"] is None


def test_filtra_por_municipio(client):
    sembrar(client, listing(), listing(url="https://ejemplo/2", municipio="parla"))
    body = client.get("/listings", params={"municipio": "parla"}).json()
    assert [b["municipio"] for b in body] == ["parla"]


def test_por_defecto_no_incluye_retirados(client, hoy):
    hoy["fecha"] = date(2026, 9, 1)
    sembrar(client, listing(url="https://ejemplo/viejo"))
    hoy["fecha"] = date(2026, 9, 29)
    sembrar(client, listing(url="https://ejemplo/nuevo"))
    activos = client.get("/listings").json()
    assert [a["url"] for a in activos] == ["https://ejemplo/nuevo"]
    todos = client.get("/listings", params={"incluir_retirados": True}).json()
    assert {a["url"] for a in todos} == {"https://ejemplo/viejo", "https://ejemplo/nuevo"}
    assert {a["estado"] for a in todos} == {"activo", "retirado"}


def test_ordenados_por_score_descendente_y_sin_score_al_final(client):
    sembrar(
        client,
        listing(url="https://ejemplo/a", score=10.0),
        listing(url="https://ejemplo/b", score=90.0),
        listing(url="https://ejemplo/c", m2=None),
    )
    urls = [x["url"] for x in client.get("/listings").json()]
    assert urls == ["https://ejemplo/b", "https://ejemplo/a", "https://ejemplo/c"]


def test_sirve_el_detalle_que_usa_el_dashboard(client):
    sembrar(
        client,
        listing(detalle={"score_details": ["Valor vs zona (+20)"], "eur_m2": 1900}),
    )
    (it,) = client.get("/listings").json()
    assert it["detalle"]["eur_m2"] == 1900
    assert it["detalle"]["score_details"] == ["Valor vs zona (+20)"]
