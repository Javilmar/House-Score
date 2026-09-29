"""Regla de bajada de precio migrada de listings_store._aplicar_precio (T027, unidad)."""

from app.services.reglas import EstadoPrecio, aplicar_precio


def viejo(precio=100000, anterior=None, bajada=None, candidato=None):
    return EstadoPrecio(precio=precio, anterior=anterior, bajada=bajada, candidato=candidato)


def test_bajada_normal_se_acepta_y_registra_historial():
    r = aplicar_precio(viejo(100000), 90000)
    assert (r.estado.precio, r.estado.anterior, r.estado.bajada) == (90000, 100000, 10000)
    assert r.bajada_confirmada is True


def test_subida_o_igual_limpia_marcas_de_bajada():
    r = aplicar_precio(viejo(100000, anterior=110000, bajada=10000), 100000)
    assert r.estado.bajada is None and r.estado.anterior is None
    assert r.bajada_confirmada is False


def test_bajada_mayor_al_40_por_ciento_queda_como_candidata():
    r = aplicar_precio(viejo(100000), 50000)
    assert r.estado.precio == 100000
    assert r.estado.candidato == 50000
    assert r.bajada_confirmada is False


def test_bajada_grande_se_confirma_con_valor_igual_en_la_pasada_siguiente():
    r = aplicar_precio(viejo(100000, candidato=50000), 50000)
    assert (r.estado.precio, r.estado.bajada, r.estado.anterior) == (50000, 50000, 100000)
    assert r.estado.candidato is None
    assert r.bajada_confirmada is True


def test_precio_nuevo_ausente_conserva_estado_anterior():
    r = aplicar_precio(viejo(100000, anterior=110000, bajada=10000, candidato=70000), None)
    assert r.estado == viejo(100000, anterior=110000, bajada=10000, candidato=70000)
    assert r.bajada_confirmada is False


def test_sin_precio_previo_acepta_el_nuevo():
    r = aplicar_precio(viejo(None), 90000)
    assert r.estado.precio == 90000 and r.estado.bajada is None
