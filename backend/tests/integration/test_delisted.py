"""T029 - FR-007: sin aparecer 7 dias => retirado; reaparece => activo."""

from datetime import date

from tests.conftest import AUTH
from tests.factories import listing, pasada


def enviar(client, hoy, fecha, *items):
    hoy["fecha"] = fecha
    return client.post("/ingest", json=pasada(*items), headers=AUTH)


def estados(client):
    body = client.get("/listings", params={"incluir_retirados": True}).json()
    return {b["url"]: b["estado"] for b in body}


def test_a_los_7_dias_sin_aparecer_pasa_a_retirado(client, hoy):
    enviar(client, hoy, date(2026, 9, 1), listing(url="https://e/a"), listing(url="https://e/b"))
    r = enviar(client, hoy, date(2026, 9, 7), listing(url="https://e/b"))  # a: 6 dias
    assert r.json()["retirados"] == 0
    assert estados(client)["https://e/a"] == "activo"
    r = enviar(client, hoy, date(2026, 9, 8), listing(url="https://e/b"))  # a: 7 dias
    assert r.json()["retirados"] == 1
    assert estados(client) == {"https://e/a": "retirado", "https://e/b": "activo"}


def test_retirado_ya_marcado_no_se_cuenta_de_nuevo(client, hoy):
    enviar(client, hoy, date(2026, 9, 1), listing(url="https://e/a"), listing(url="https://e/b"))
    enviar(client, hoy, date(2026, 9, 8), listing(url="https://e/b"))
    r = enviar(client, hoy, date(2026, 9, 9), listing(url="https://e/b"))
    assert r.json()["retirados"] == 0


def test_reaparece_y_se_reactiva(client, hoy):
    enviar(client, hoy, date(2026, 9, 1), listing(url="https://e/a"), listing(url="https://e/b"))
    enviar(client, hoy, date(2026, 9, 8), listing(url="https://e/b"))
    assert estados(client)["https://e/a"] == "retirado"
    enviar(client, hoy, date(2026, 9, 10), listing(url="https://e/a"))
    assert estados(client)["https://e/a"] == "activo"


def test_el_agregado_diario_solo_cuenta_activos(client, hoy):
    enviar(client, hoy, date(2026, 9, 1), listing(url="https://e/a"), listing(url="https://e/b"))
    enviar(client, hoy, date(2026, 9, 8), listing(url="https://e/b"))
    ult = client.get("/historico").json()[-1]
    assert ult["fecha"] == "2026-09-08" and ult["total_listings"] == 1
