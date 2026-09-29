"""T019 - FR-005: sin m2 fiables => datos_insuficientes y sin score."""

from app.services.reglas import normalizar_listing


def test_sin_m2_queda_datos_insuficientes_y_sin_score():
    r = normalizar_listing({"url": "u", "municipio": "getafe", "m2": None, "score": 50.0})
    assert r["datos_insuficientes"] is True
    assert r["score"] is None
    assert r["m2"] is None


def test_m2_cero_equivale_a_ausente():
    # los JSON actuales representan "sin m2" como 0
    r = normalizar_listing({"url": "u", "municipio": "getafe", "m2": 0, "score": 12})
    assert r["datos_insuficientes"] is True
    assert r["score"] is None
    assert r["m2"] is None


def test_flag_del_scorer_se_respeta_aunque_haya_m2():
    r = normalizar_listing(
        {"url": "u", "municipio": "getafe", "m2": 80, "score": 43, "datos_insuficientes": True}
    )
    assert r["datos_insuficientes"] is True
    assert r["score"] is None
    assert r["m2"] == 80


def test_con_m2_fiable_conserva_score():
    r = normalizar_listing({"url": "u", "municipio": "getafe", "m2": 80, "score": 61.5})
    assert r["datos_insuficientes"] is False
    assert r["score"] == 61.5


def test_municipio_ausente_no_es_nulo():
    r = normalizar_listing({"url": "u", "m2": 80, "score": 1})
    assert r["municipio"] == "desconocido"
