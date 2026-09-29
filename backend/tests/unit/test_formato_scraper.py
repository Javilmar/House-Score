"""Mapeo del formato del scraper (campos en ingles) al contrato de la API."""

from app.services.formato_scraper import payload_desde_scraper

ITEM = {
    "title": "Piso en Getafe",
    "price": 180000,
    "score": 71,
    "location": "Centro, Getafe",
    "m2": 80,
    "rooms": 3,
    "bathrooms": 2,
    "url": "https://www.pisos.com/x",
    "source": "pisos.com",
    "municipio": "getafe",
    "datos_insuficientes": False,
    "score_details": ["Valor vs zona (+20)"],
    "eur_m2": 2250,
    "description": "texto",
    # estado propio del almacen: no debe viajar en el detalle
    "first_seen": "2026-07-14",
    "last_seen": "2026-09-08",
    "status": "active",
    "price_drop": 5000,
    "previous_price": 185000,
    "_candidate_price": 100,
}


def test_mapea_los_campos_principales():
    p = payload_desde_scraper(ITEM)
    assert p["url"] == "https://www.pisos.com/x"
    assert p["titulo"] == "Piso en Getafe"
    assert p["precio"] == 180000
    assert p["m2"] == 80
    assert p["habitaciones"] == 3
    assert p["banos"] == 2
    assert p["municipio"] == "getafe"
    assert p["fuente"] == "pisos.com"
    assert p["score"] == 71
    assert p["datos_insuficientes"] is False


def test_el_resto_de_campos_va_al_detalle_sin_el_estado_del_almacen():
    d = payload_desde_scraper(ITEM)["detalle"]
    assert d["score_details"] == ["Valor vs zona (+20)"]
    assert d["eur_m2"] == 2250
    assert d["location"] == "Centro, Getafe"
    for estado in ("first_seen", "last_seen", "status", "price_drop", "previous_price"):
        assert estado not in d
    assert "_candidate_price" not in d
    assert "title" not in d and "price" not in d
