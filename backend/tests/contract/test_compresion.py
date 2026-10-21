"""T-gzip - /listings se comprime con gzip cuando el cliente lo admite y el cuerpo es grande."""

from tests.conftest import AUTH
from tests.factories import listing, pasada

FRONT = "https://housescore.pages.dev"


def sembrar(client, n):
    items = [listing(url=f"https://ejemplo/{i}") for i in range(n)]
    r = client.post("/ingest", json=pasada(*items), headers=AUTH)
    assert r.status_code == 201, r.text


def test_respuesta_grande_va_comprimida_si_el_cliente_admite_gzip(client):
    sembrar(client, 20)
    r = client.get("/listings", headers={"Accept-Encoding": "gzip"})
    assert r.headers["content-encoding"] == "gzip"
    assert len(r.json()) == 20  # el cliente la descomprime de forma transparente


def test_sin_accept_encoding_no_se_comprime(client):
    sembrar(client, 20)
    r = client.get("/listings", headers={"Accept-Encoding": "identity"})
    assert "content-encoding" not in r.headers


def test_cuerpo_menor_que_el_minimo_no_se_comprime(client):
    r = client.get("/listings", headers={"Accept-Encoding": "gzip"})
    assert "content-encoding" not in r.headers


def test_convive_con_cors(make_client):
    c = make_client(CORS_ORIGINS=FRONT)
    sembrar(c, 20)
    r = c.get("/listings", headers={"Accept-Encoding": "gzip", "Origin": FRONT})
    assert r.headers["content-encoding"] == "gzip"
    assert r.headers["access-control-allow-origin"] == FRONT
