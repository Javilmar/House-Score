"""T039 - cliente del scraper que envia una pasada a POST /ingest."""

import json

import httpx
import pytest

from worker.scraper.client import IngestError, enviar_pasada, main

ITEM = {
    "title": "Piso",
    "price": 100000,
    "score": 50,
    "m2": 70,
    "rooms": 2,
    "bathrooms": 1,
    "url": "https://e/1",
    "source": "pisos.com",
    "municipio": "getafe",
    "datos_insuficientes": False,
    "eur_m2": 1428,
}
RESUMEN = {
    "listings_procesados": 1,
    "nuevos": 1,
    "actualizados": 0,
    "descartados_bloqueados": 0,
    "retirados": 0,
}


def cliente(handler):
    return httpx.Client(transport=httpx.MockTransport(handler), base_url="http://api.test")


def test_envia_el_formato_de_la_api_con_el_secreto():
    vistos = []

    def handler(req: httpx.Request):
        vistos.append(req)
        return httpx.Response(201, json=RESUMEN)

    r = enviar_pasada([ITEM], "s3cret", http=cliente(handler), espera=0)
    assert r == RESUMEN
    (req,) = vistos
    assert req.url.path == "/ingest"
    assert req.headers["authorization"] == "Bearer s3cret"
    (enviado,) = json.loads(req.content)["listings"]
    assert enviado["titulo"] == "Piso" and enviado["precio"] == 100000
    assert enviado["detalle"] == {"eur_m2": 1428}


def test_reintenta_ante_errores_de_servidor_y_conexion():
    intentos = []

    def handler(req):
        intentos.append(1)
        if len(intentos) == 1:
            raise httpx.ConnectError("sin conexion")
        if len(intentos) == 2:
            return httpx.Response(503)
        return httpx.Response(201, json=RESUMEN)

    assert enviar_pasada([ITEM], "s", http=cliente(handler), espera=0) == RESUMEN
    assert len(intentos) == 3


def test_no_reintenta_si_el_secreto_es_incorrecto():
    intentos = []

    def handler(req):
        intentos.append(1)
        return httpx.Response(401, json={"detail": "no autorizado"})

    with pytest.raises(IngestError, match="401"):
        enviar_pasada([ITEM], "mal", http=cliente(handler), espera=0)
    assert len(intentos) == 1


def test_falla_tras_agotar_los_reintentos():
    def handler(req):
        return httpx.Response(500)

    with pytest.raises(IngestError):
        enviar_pasada([ITEM], "s", http=cliente(handler), reintentos=3, espera=0)


def test_ignora_entradas_sin_url():
    vistos = []

    def handler(req):
        vistos.append(json.loads(req.content))
        return httpx.Response(201, json=RESUMEN)

    enviar_pasada([ITEM, {"title": "sin url"}], "s", http=cliente(handler), espera=0)
    assert len(vistos[0]["listings"]) == 1


def test_cli_lee_el_archivo_y_devuelve_0(tmp_path, monkeypatch, capsys):
    archivo = tmp_path / "pasada.json"
    archivo.write_text(json.dumps([ITEM]), encoding="utf-8")
    monkeypatch.setenv("INGEST_SECRET", "s")

    def handler(req):
        return httpx.Response(201, json=RESUMEN)

    assert main([str(archivo)], http=cliente(handler)) == 0
    assert "nuevos" in capsys.readouterr().out


def test_cli_devuelve_distinto_de_0_si_falla(tmp_path, monkeypatch, capsys):
    archivo = tmp_path / "pasada.json"
    archivo.write_text(json.dumps([ITEM]), encoding="utf-8")
    monkeypatch.setenv("INGEST_SECRET", "s")

    def handler(req):
        return httpx.Response(401)

    assert main([str(archivo)], http=cliente(handler)) == 1
    assert "401" in capsys.readouterr().err


def test_cli_sin_secreto_falla_sin_llamar_a_la_api(tmp_path, monkeypatch, capsys):
    archivo = tmp_path / "pasada.json"
    archivo.write_text("[]", encoding="utf-8")
    monkeypatch.delenv("INGEST_SECRET", raising=False)
    assert main([str(archivo)]) == 2
    assert "INGEST_SECRET" in capsys.readouterr().err
