"""T026 - FR-009/SC-005: misma pasada dos veces no duplica."""

import threading
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker

from app.models import Listing
from app.schemas import ListingIn
from app.services.ingest_service import ingest_pasada
from tests.conftest import AUTH, HOY
from tests.factories import listing, pasada


def test_misma_pasada_dos_veces_no_duplica(client):
    p = pasada(listing(), listing(url="https://ejemplo/2"))
    r1 = client.post("/ingest", json=p, headers=AUTH)
    r2 = client.post("/ingest", json=p, headers=AUTH)
    assert r1.json()["nuevos"] == 2
    assert r2.json()["nuevos"] == 0 and r2.json()["actualizados"] == 2
    assert len(client.get("/listings").json()) == 2


def test_url_repetida_dentro_de_una_pasada_cuenta_una_vez(client):
    r = client.post("/ingest", json=pasada(listing(precio=1), listing(precio=2)), headers=AUTH)
    assert r.json()["listings_procesados"] == 1
    (it,) = client.get("/listings").json()
    assert it["precio"] == 2  # gana la ultima aparicion


def test_actualiza_score_y_conserva_primera_aparicion(client, hoy):
    hoy["fecha"] = date(2026, 9, 1)
    client.post("/ingest", json=pasada(listing(score=10.0)), headers=AUTH)
    hoy["fecha"] = date(2026, 9, 5)
    client.post("/ingest", json=pasada(listing(score=55.0)), headers=AUTH)
    (it,) = client.get("/listings").json()
    assert it["score"] == 55.0
    assert it["primera_aparicion"] == "2026-09-01"
    assert it["ultima_aparicion"] == "2026-09-05"


def test_dos_pasadas_simultaneas_no_crean_duplicados(engine):
    maker = sessionmaker(bind=engine, expire_on_commit=False)
    items = [ListingIn(**listing(url=f"https://e/{i}")) for i in range(30)]
    errores = []

    def correr():
        try:
            with maker() as s:
                ingest_pasada(s, items, HOY)
        except Exception as e:  # pragma: no cover - se reporta abajo
            errores.append(e)

    hilos = [threading.Thread(target=correr) for _ in range(2)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()
    assert errores == []
    with maker() as s:
        assert s.scalar(select(func.count()).select_from(Listing)) == 30
