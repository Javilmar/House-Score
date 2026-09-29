"""T037 / FR-014 - los fallos de ingesta quedan en el log y no dejan datos a medias."""

import logging

from tests.conftest import AUTH
from tests.factories import listing, pasada


def test_fallo_de_persistencia_devuelve_500_hace_rollback_y_deja_log(client, monkeypatch, caplog):
    from app.services import ingest_service

    def boom(*a, **k):
        raise RuntimeError("fallo simulado de BBDD")

    with monkeypatch.context() as m:
        m.setattr(ingest_service, "actualizar_pasada_diaria", boom)
        with caplog.at_level(logging.ERROR, logger="housescore.ingest"):
            r = client.post("/ingest", json=pasada(listing()), headers=AUTH)
    assert r.status_code == 500
    registros = [rec for rec in caplog.records if rec.name == "housescore.ingest"]
    assert registros, "el fallo debe quedar registrado"
    assert any("fallo simulado" in rec.getMessage() or rec.exc_info for rec in registros)

    assert client.get("/listings").json() == []  # nada persistido a medias
