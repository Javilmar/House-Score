"""T027 - bajadas de precio: >40% se confirma con la pasada siguiente."""

from datetime import date

from sqlalchemy import select

from app.models import HistorialPrecio
from tests.conftest import AUTH
from tests.factories import listing, pasada


def enviar(client, hoy, dia, **over):
    hoy["fecha"] = date(2026, 9, dia)
    r = client.post("/ingest", json=pasada(listing(**over)), headers=AUTH)
    assert r.status_code == 201
    return client.get("/listings").json()[0]


def test_bajada_normal_queda_registrada(client, hoy, session):
    enviar(client, hoy, 1, precio=100000)
    it = enviar(client, hoy, 2, precio=90000)
    assert it["precio"] == 90000
    assert it["bajada_precio"] == 10000 and it["precio_anterior"] == 100000
    (h,) = session.scalars(select(HistorialPrecio)).all()
    assert (h.precio_anterior, h.precio_nuevo, h.fecha_cambio) == (100000, 90000, date(2026, 9, 2))


def test_bajada_mayor_al_40_no_se_acepta_hasta_confirmarse(client, hoy, session):
    enviar(client, hoy, 1, precio=100000)
    it = enviar(client, hoy, 2, precio=50000)
    assert it["precio"] == 100000  # se mantiene el precio anterior
    assert it["bajada_precio"] is None
    assert session.scalars(select(HistorialPrecio)).all() == []

    it = enviar(client, hoy, 3, precio=50000)  # se confirma
    assert it["precio"] == 50000 and it["bajada_precio"] == 50000
    assert len(session.scalars(select(HistorialPrecio)).all()) == 1


def test_bajada_grande_no_confirmada_se_descarta_si_el_precio_vuelve(client, hoy, session):
    enviar(client, hoy, 1, precio=100000)
    enviar(client, hoy, 2, precio=50000)
    it = enviar(client, hoy, 3, precio=100000)
    assert it["precio"] == 100000 and it["bajada_precio"] is None
    assert session.scalars(select(HistorialPrecio)).all() == []


def test_reintento_el_mismo_dia_no_duplica_historial_ni_pierde_la_marca(client, hoy, session):
    enviar(client, hoy, 1, precio=100000)
    enviar(client, hoy, 2, precio=90000)
    it = enviar(client, hoy, 2, precio=90000)  # reintento manual de la misma pasada
    assert it["bajada_precio"] == 10000
    assert len(session.scalars(select(HistorialPrecio)).all()) == 1


def test_reintento_del_mismo_dia_no_confirma_una_bajada_candidata(client, hoy, session):
    enviar(client, hoy, 1, precio=100000)
    enviar(client, hoy, 2, precio=50000)  # candidata
    it = enviar(client, hoy, 2, precio=50000)  # reintento de la misma pasada
    assert it["precio"] == 100000 and it["bajada_precio"] is None
    assert session.scalars(select(HistorialPrecio)).all() == []


def test_pasada_sin_precio_conserva_el_anterior(client, hoy):
    enviar(client, hoy, 1, precio=100000)
    it = enviar(client, hoy, 2, precio=None)
    assert it["precio"] == 100000
