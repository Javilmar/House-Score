"""T023 - migracion one-off de frontend/datos y frontend/config (SC-004)."""

import json
from datetime import date

import pytest
from sqlalchemy import func, select

from app.models import HistorialPrecio, Listing, PasadaDiaria, PrecioReferencia
from app.services.migracion import BaseDeDatosNoVacia, migrar


def item(url, **over):
    base = {
        "title": f"Piso {url}",
        "price": 100000,
        "score": 50,
        "location": "loc",
        "m2": 70,
        "rooms": 2,
        "bathrooms": 1,
        "url": url,
        "source": "pisos.com",
        "municipio": "getafe",
        "datos_insuficientes": False,
        "score_details": ["a (+1)"],
        "eur_m2": 1428,
        "first_seen": "2026-07-14",
        "last_seen": "2026-09-08",
        "status": "active",
    }
    base.update(over)
    return base


@pytest.fixture
def carpetas(tmp_path):
    datos = tmp_path / "datos"
    config = tmp_path / "config"
    datos.mkdir()
    config.mkdir()
    listings = [
        item("https://e/a"),
        item("https://e/b", price=90000, previous_price=100000, price_drop=10000),
        item("https://e/c", m2=0, score=12, datos_insuficientes=True),
        item("https://e/d", status="delisted", last_seen="2026-08-01"),
        item("https://e/e", _candidate_price=40000),
    ]
    (datos / "listings.json").write_text(json.dumps(listings), encoding="utf-8")
    historico = [
        {
            "fecha": "2026-09-07",
            "count": 5,
            "avg_price": 98000,
            "avg_score": 40.5,
            "min_price": 50000,
            "max_price": 150000,
        },
        {
            "fecha": "2026-09-08",
            "count": 4,
            "avg_price": 99000,
            "avg_score": 41.0,
            "min_price": 51000,
            "max_price": 151000,
        },
    ]
    (datos / "historico_diario.json").write_text(json.dumps(historico), encoding="utf-8")
    (config / "precios_referencia.json").write_text(
        json.dumps(
            {
                "updated": "2026-09-08",
                "municipios": {
                    "getafe": {"eur_m2": 2100, "n": 30},
                    "parla": {"eur_m2": 1500, "n": 9},
                },
                "zonas": {},
            }
        ),
        encoding="utf-8",
    )
    # pasada posterior a listings.json: se repite a traves de la ingesta
    (datos / "2026-09-09.json").write_text(
        json.dumps([item("https://e/a", price=95000, score=60), item("https://e/nuevo")]),
        encoding="utf-8",
    )
    # pasada anterior al estado base: no se repite
    (datos / "2026-09-01.json").write_text(json.dumps([item("https://e/viejo")]), encoding="utf-8")
    return datos, config


def test_migra_todos_los_listings_sin_perdida(session, carpetas):
    datos, config = carpetas
    r = migrar(session, datos, config)
    urls = set(session.scalars(select(Listing.url)))
    assert {"https://e/a", "https://e/b", "https://e/c", "https://e/d", "https://e/e"} <= urls
    assert "https://e/viejo" not in urls
    assert r["listings_base"] == 5


def test_conserva_fechas_estado_y_marcas_de_precio(session, carpetas):
    datos, config = carpetas
    migrar(session, datos, config)
    por_url = {li.url: li for li in session.scalars(select(Listing))}
    b = por_url["https://e/b"]
    assert (b.precio, b.precio_anterior, b.bajada_precio) == (90000, 100000, 10000)
    assert b.primera_aparicion == date(2026, 7, 14)
    assert por_url["https://e/d"].estado == "retirado"
    assert por_url["https://e/e"].precio_candidato == 40000
    (h,) = [h for h in session.scalars(select(HistorialPrecio)) if h.listing_id == b.id]
    assert (h.precio_anterior, h.precio_nuevo) == (100000, 90000)


def test_aplica_las_reglas_de_datos_insuficientes(session, carpetas):
    datos, config = carpetas
    migrar(session, datos, config)
    c = session.scalars(select(Listing).where(Listing.url == "https://e/c")).one()
    assert c.datos_insuficientes is True and c.score is None and c.m2 is None


def test_guarda_el_detalle_del_dashboard(session, carpetas):
    datos, config = carpetas
    migrar(session, datos, config)
    a = session.scalars(select(Listing).where(Listing.url == "https://e/a")).one()
    assert a.detalle["score_details"] == ["a (+1)"] and a.detalle["eur_m2"] == 1428


def test_migra_el_historico_diario(session, carpetas):
    datos, config = carpetas
    migrar(session, datos, config)
    f = session.get(PasadaDiaria, date(2026, 9, 7))
    assert (f.total_listings, f.precio_medio, f.score_medio) == (5, 98000, 40.5)
    assert (f.precio_min, f.precio_max) == (50000, 150000)


def test_repite_las_pasadas_posteriores_al_estado_base(session, carpetas):
    datos, config = carpetas
    r = migrar(session, datos, config)
    assert r["pasadas_repetidas"] == ["2026-09-09"]
    por_url = {li.url: li for li in session.scalars(select(Listing))}
    assert por_url["https://e/a"].precio == 95000  # bajada normal aplicada por la ingesta
    assert por_url["https://e/a"].ultima_aparicion == date(2026, 9, 9)
    assert "https://e/nuevo" in por_url
    # el agregado de ese dia lo calcula la ingesta
    assert session.get(PasadaDiaria, date(2026, 9, 9)) is not None


def test_migra_precios_de_referencia(session, carpetas):
    datos, config = carpetas
    migrar(session, datos, config)
    assert session.get(PrecioReferencia, "getafe").mediana_eur_m2 == 2100
    assert session.get(PrecioReferencia, "parla").mediana_eur_m2 == 1500


def test_no_migra_sobre_una_base_con_datos(session, carpetas):
    datos, config = carpetas
    migrar(session, datos, config)
    with pytest.raises(BaseDeDatosNoVacia):
        migrar(session, datos, config)
    assert session.scalar(select(func.count()).select_from(Listing)) == 6


def test_falla_si_falta_listings_json(session, tmp_path):
    with pytest.raises(FileNotFoundError):
        migrar(session, tmp_path, tmp_path)
