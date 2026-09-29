"""T038/T040 - conexion del scorer con la API: historial, comprobacion previa y publicacion."""

import json
from datetime import date

import httpx
import pytest

from worker.scraper.client import IngestError
from worker.scraper.publicar import cargar_historial_api, publicar_pasada, verificar_api

ITEM = {"title": "Piso", "price": 1, "url": "https://e/1", "m2": 70, "municipio": "getafe"}
RESUMEN = {
    "listings_procesados": 1,
    "nuevos": 1,
    "actualizados": 0,
    "descartados_bloqueados": 0,
    "retirados": 0,
}


def cliente(handler):
    return httpx.Client(transport=httpx.MockTransport(handler), base_url="http://api.test")


def test_historial_desde_la_api_incluye_retirados_y_usa_el_formato_del_scorer():
    vistos = []

    def handler(req: httpx.Request):
        vistos.append(req)
        return httpx.Response(
            200,
            json=[
                {"url": "https://e/a", "primera_aparicion": "2026-07-14", "precio": 100000},
                {"url": "https://e/b", "primera_aparicion": "2026-08-01", "precio": None},
            ],
        )

    h = cargar_historial_api(http=cliente(handler))
    assert vistos[0].url.params["incluir_retirados"] == "true"
    assert h == {
        "https://e/a": {"first_seen": "2026-07-14", "price": 100000},
        "https://e/b": {"first_seen": "2026-08-01", "price": None},
    }


def test_historial_falla_alto_si_la_api_no_responde():
    def handler(req):
        raise httpx.ConnectError("caida")

    with pytest.raises(IngestError, match="historial"):
        cargar_historial_api(http=cliente(handler))


def test_verificar_api_ok_y_caida():
    verificar_api(http=cliente(lambda r: httpx.Response(200, json=[])))

    def caida(req):
        raise httpx.ConnectError("caida")

    with pytest.raises(IngestError, match="no responde"):
        verificar_api(http=cliente(caida))


def test_publicar_pasada_envia_y_no_deja_pendientes(tmp_path):
    def handler(req):
        return httpx.Response(201, json=RESUMEN)

    r = publicar_pasada(
        [ITEM], "madrid", http=cliente(handler), secreto="s", pendientes=tmp_path, espera=0
    )
    assert r == RESUMEN
    assert list(tmp_path.iterdir()) == []


def test_publicar_pasada_fallida_guarda_copia_para_reenviar(tmp_path):
    def handler(req):
        return httpx.Response(503)

    with pytest.raises(IngestError):
        publicar_pasada(
            [ITEM],
            "toledo",
            fecha=date(2026, 9, 29),
            http=cliente(handler),
            secreto="s",
            pendientes=tmp_path,
            espera=0,
        )
    (copia,) = tmp_path.iterdir()
    assert copia.name == "2026-09-29-toledo.json"
    # se puede reenviar tal cual con `python -m worker.scraper.client`
    assert json.loads(copia.read_text(encoding="utf-8")) == [ITEM]


def test_publicar_sin_secreto_falla_sin_llamar_a_la_api(tmp_path, monkeypatch):
    monkeypatch.delenv("INGEST_SECRET", raising=False)
    llamadas = []

    def handler(req):
        llamadas.append(req)
        return httpx.Response(201, json=RESUMEN)

    with pytest.raises(IngestError, match="INGEST_SECRET"):
        publicar_pasada([ITEM], "madrid", http=cliente(handler), pendientes=tmp_path)
    assert llamadas == []
    assert len(list(tmp_path.iterdir())) == 1  # la pasada no se pierde
