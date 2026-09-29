"""T025 - POST /ingest exige el secreto compartido (FR-010/FR-011)."""

import pytest

from tests.factories import listing, pasada


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"Authorization": "Bearer otro-secreto"},
        {"Authorization": "test-secret"},
        {"Authorization": "Basic test-secret"},
        {"Authorization": "Bearer "},
    ],
)
def test_sin_secreto_correcto_devuelve_401(client, headers):
    r = client.post("/ingest", json=pasada(), headers=headers)
    assert r.status_code == 401


def test_no_se_persiste_nada_si_no_hay_auth(client):
    client.post("/ingest", json=pasada(listing()))
    assert client.get("/listings").json() == []


def test_si_no_hay_secreto_configurado_se_rechaza_todo(make_client):
    c = make_client(INGEST_SECRET="")
    r = c.post("/ingest", json=pasada(), headers={"Authorization": "Bearer "})
    assert r.status_code == 401
    r = c.post("/ingest", json=pasada(), headers={"Authorization": "Bearer test-secret"})
    assert r.status_code == 401
