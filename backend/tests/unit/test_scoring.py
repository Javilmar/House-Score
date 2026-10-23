"""Scoring del exterior, reutilización de la ficha, topes por zona y anuncios problemáticos."""

from datetime import date

from worker.scraper import property_scorer_common as c

HOY = date(2026, 10, 22)


def piso(**over):
    base = {
        "title": "Piso en Getafe",
        "location": "Centro (Getafe)",
        "url": "https://e/1",
        "price": 150000,
        "size_m2": 90,
        "bedrooms": 3,
        "municipio": "getafe",
        "first_seen": "2026-10-22",
    }
    base.update(over)
    return base


def test_exterior_detectado_en_el_titulo_suma():
    p = c.score_property(piso(title="Piso con terraza"), today=HOY)
    assert p["exterior"] is True
    assert "🌿 Espacio exterior (+12)" in p["score_details"]


def test_sin_ficha_el_exterior_no_penaliza_y_con_ficha_si():
    extras = {"size_m2": 140, "description": "Con piscina, garaje y trastero. Cerca del metro."}
    sin_ficha = c.score_property(piso(**extras), today=HOY)
    con_ficha = c.score_property(piso(ficha_detalle=True, **extras), today=HOY)
    assert "❔ Exterior sin verificar (0)" in sin_ficha["score_details"]
    assert "⚠️ Sin exterior en la ficha (-25 pts)" in con_ficha["score_details"]
    # misma base: sin la penalización el score es 25 puntos mayor (no recortado por 0 ni 100)
    assert 25 < sin_ficha["score"] < 100
    assert sin_ficha["score"] - con_ficha["score"] == 25


def historial(**detalle):
    return {"https://e/1": {"first_seen": "2026-10-01", "price": 145000, "detalle": detalle}}


def test_reutiliza_la_ficha_y_su_precio_si_el_listado_no_cambia():
    h = historial(ficha_detalle=True, detail_features={"terraza": True}, precio_listado=150000)
    prop = piso(price=150000, precio_listado=150000)
    assert c.reutilizar_ficha(prop, h) is True
    assert prop["price"] == 145000
    assert prop["detail_features"] == {"terraza": True}
    assert prop["ficha_detalle"] is True


def test_si_el_listado_cambia_de_precio_se_queda_el_nuevo():
    h = historial(ficha_detalle=True, detail_features={"terraza": True}, precio_listado=150000)
    prop = piso(price=140000, precio_listado=140000)
    assert c.reutilizar_ficha(prop, h) is True
    assert prop["price"] == 140000


def test_sin_ficha_en_el_historial_no_toca_el_listing():
    prop = piso(precio_listado=150000)
    antes = dict(prop)
    assert c.reutilizar_ficha(prop, historial(detail_features={"terraza": True})) is False
    assert prop == antes


def test_candidatos_ficha_salta_los_que_ya_tienen_ficha_y_respeta_el_limite():
    listings = [
        piso(url="a", score=90, ficha_detalle=True),
        piso(url="b", score=80),
        piso(url="c", score=70),
        piso(url="d", score=60),
    ]
    assert [p["url"] for p in c.candidatos_ficha(listings, 2)] == ["b", "c"]


def test_tope_por_zona():
    assert c.tope_de("getafe") == 300_000
    assert c.tope_de("alcala_de_henares") == 350_000
    assert c.tope_de("rivas_vaciamadrid") == 300_000
    assert c.tope_de("tres_cantos") == 400_000
    assert c.tope_de("illescas") == 300_000
    assert c.tope_de("desconocido") == 300_000  # el más bajo: nunca se cuela un piso caro


def test_cada_municipio_pertenece_a_una_sola_zona():
    todos = [m for z in c.ZONAS.values() for m in z.municipios]
    assert len(todos) == len(set(todos))


def test_problematicos():
    for texto in ("Vivienda sin posesión", "Piso ocupado", "Inmueble okupado",
                  "Venta de nuda propiedad", "Procedente de subasta", "No admite visitas"):
        assert c.es_problematico(piso(description=texto)), texto
    for texto in ("Piso desocupado y listo para entrar", "Entrega inmediata", ""):
        assert not c.es_problematico(piso(description=texto)), texto
