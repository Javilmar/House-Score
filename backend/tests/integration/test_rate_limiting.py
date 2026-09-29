"""T046 - FR-012: rate limiting por IP en los endpoints de lectura."""

from tests.conftest import AUTH
from tests.factories import pasada


def test_supera_el_limite_devuelve_429(make_client):
    c = make_client(RATE_LIMIT="3/minute")
    codigos = [c.get("/listings").status_code for _ in range(5)]
    assert codigos[:3] == [200, 200, 200]
    assert 429 in codigos[3:]


def test_el_limite_es_por_ip_real_detras_del_tunel(make_client):
    c = make_client(RATE_LIMIT="2/minute")
    a = {"CF-Connecting-IP": "203.0.113.1"}
    b = {"CF-Connecting-IP": "203.0.113.2"}
    assert [c.get("/listings", headers=a).status_code for _ in range(3)] == [200, 200, 429]
    assert c.get("/listings", headers=b).status_code == 200


def test_historico_tambien_limitado(make_client):
    c = make_client(RATE_LIMIT="1/minute")
    assert c.get("/historico").status_code == 200
    assert c.get("/historico").status_code == 429


def test_ingest_no_esta_sujeto_al_rate_limit_de_lectura(make_client):
    c = make_client(RATE_LIMIT="1/minute")
    for _ in range(5):
        assert c.post("/ingest", json=pasada(), headers=AUTH).status_code == 201
