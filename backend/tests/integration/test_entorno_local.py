"""T041 - tras `docker compose up`, la API responde (Escenario 1 de quickstart.md).

Solo se ejecuta contra un entorno ya levantado: define HOUSESCORE_E2E_URL
(p. ej. http://localhost:8000). Sin la variable, se omite.
"""

import os

import httpx
import pytest

URL = os.environ.get("HOUSESCORE_E2E_URL")

pytestmark = pytest.mark.skipif(not URL, reason="define HOUSESCORE_E2E_URL para probar el entorno")


def test_la_api_responde_con_listings_y_historico():
    assert httpx.get(f"{URL}/listings", timeout=10).status_code == 200
    assert httpx.get(f"{URL}/historico", timeout=10).status_code == 200


def test_ingest_exige_secreto():
    r = httpx.post(f"{URL}/ingest", json={"listings": []}, timeout=10)
    assert r.status_code == 401
