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

    t = [0.0]

    def dormir(s):
        t[0] += s

    with pytest.raises(IngestError, match="no responde"):
        verificar_api(http=cliente(caida), dormir=dormir, ahora=lambda: t[0])


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


class Reloj:
    """Reloj y sleep falsos: dormir avanza el reloj, así los tests no esperan de verdad."""

    def __init__(self):
        self.t = 0.0
        self.esperas = []

    def ahora(self):
        return self.t

    def dormir(self, s):
        self.esperas.append(s)
        self.t += s


def test_verificar_api_espera_a_que_despierte_la_api():
    reloj = Reloj()
    llamadas = []

    def handler(req):
        llamadas.append(1)
        if len(llamadas) < 4:
            return httpx.Response(503)
        return httpx.Response(200, json=[])

    verificar_api(http=cliente(handler), dormir=reloj.dormir, ahora=reloj.ahora)
    assert len(llamadas) == 4
    assert len(reloj.esperas) == 3
    assert reloj.esperas == sorted(reloj.esperas)  # esperas crecientes
    assert reloj.esperas[-1] > reloj.esperas[0]


def test_verificar_api_agota_el_presupuesto_y_nombra_url_y_tiempo():
    reloj = Reloj()

    def caida(req):
        raise httpx.ConnectError("caida")

    with pytest.raises(IngestError) as e:
        verificar_api(
            api_url="http://api.test",
            http=cliente(caida),
            dormir=reloj.dormir,
            ahora=reloj.ahora,
            presupuesto=60.0,
        )
    msg = str(e.value)
    assert "http://api.test" in msg and "no responde" in msg and "s" in msg
    assert 60.0 <= reloj.t < 60.0 + max(reloj.esperas)
    assert f"{reloj.t:.0f} s" in msg


def test_verificar_api_no_duerme_mas_alla_del_presupuesto():
    reloj = Reloj()
    with pytest.raises(IngestError):
        verificar_api(
            http=cliente(lambda r: httpx.Response(503)),
            dormir=reloj.dormir,
            ahora=reloj.ahora,
            presupuesto=20.0,
        )
    assert reloj.t <= 20.0
