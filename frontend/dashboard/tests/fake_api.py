"""API falsa para los tests del dashboard (T002).

Un servidor HTTP real en un hilo, en un puerto libre, que sirve GET /listings y
GET /historico con el contrato de specs/001-backend-api-bbdd/contracts/api.md. Permite
forzar un estado HTTP, un cuerpo inválido o un retardo, y registra las peticiones.
"""

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse


def listing_api(**over):
    """Un listing en el formato que sirve la API."""
    base = {
        "url": "https://www.pisos.com/comprar/piso-getafe-1/",
        "titulo": "Piso en Getafe",
        "precio": 180000,
        "m2": 80,
        "habitaciones": 3,
        "banos": 2,
        "municipio": "getafe",
        "fuente": "pisos.com",
        "score": 71.0,
        "datos_insuficientes": False,
        "estado": "activo",
        "primera_aparicion": "2026-09-01",
        "ultima_aparicion": "2026-09-29",
        "precio_anterior": 185000,
        "bajada_precio": 5000,
        "detalle": {
            "location": "Centro (Getafe)",
            "description": "Piso luminoso con terraza",
            "floor": "2ª planta",
            "year_built": 1998,
            "conservation": "en buen estado",
            "energy_rating": "D",
            "features": ["Ascensor", "Terraza"],
            "detail_features": {"Ascensor": True},
            "pisos_id": "123",
            "score_details": ["Valor vs zona (+20)", "Amplio: 80m2 (+10)"],
            "eur_m2": 2250,
            "exterior": True,
            "cumple_requisitos": True,
        },
    }
    base.update(over)
    return base


def listings_de_ejemplo():
    """Activo con bajada, retirado, sin datos suficientes (score nulo) y con detalle vacío."""
    return [
        listing_api(),
        listing_api(
            url="https://www.pisos.com/comprar/piso-parla-2/",
            titulo="Piso en Parla",
            municipio="parla",
            precio=140000,
            m2=70,
            score=55.0,
            estado="retirado",
            primera_aparicion="2026-07-14",
            ultima_aparicion="2026-09-10",
            precio_anterior=None,
            bajada_precio=None,
            detalle={"location": "Parla Centro (Parla)", "description": "Retirado", "eur_m2": 2000},
        ),
        listing_api(
            url="https://www.pisos.com/comprar/piso-illescas-3/",
            titulo="Piso en Illescas",
            municipio="illescas",
            precio=250000,
            m2=None,
            score=None,
            datos_insuficientes=True,
            precio_anterior=None,
            bajada_precio=None,
            detalle={"location": "El Señorío (Illescas)", "description": "Sin m2 fiables"},
        ),
        listing_api(
            url="https://www.pisos.com/comprar/piso-pinto-4/",
            titulo="Piso en Pinto",
            municipio="pinto",
            precio=120000,
            m2=60,
            score=40.0,
            precio_anterior=None,
            bajada_precio=None,
            detalle={},
        ),
    ]


def historico_de_ejemplo():
    return [
        {
            "fecha": "2026-09-27",
            "total_listings": 247,
            "score_medio": 12.44,
            "precio_medio": 223774,
            "precio_min": 29000,
            "precio_max": 441000,
        },
        {
            "fecha": "2026-09-28",
            "total_listings": 361,
            "score_medio": 12.34,
            "precio_medio": 222209,
            "precio_min": 29000,
            "precio_max": 512000,
        },
        {
            "fecha": "2026-09-29",
            "total_listings": 433,
            "score_medio": 11.48,
            "precio_medio": 224444,
            "precio_min": 29000,
            "precio_max": 700000,
        },
    ]


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # silencia el log por stderr
        pass

    def do_GET(self):
        api = self.server.api
        parsed = urlparse(self.path)
        api.peticiones.append(self.path)
        if api.retardo:
            time.sleep(api.retardo)
        ruta = parsed.path
        if ruta not in ("/listings", "/historico"):
            self.send_response(404)
            self.end_headers()
            return
        estado = api.estado.get(ruta, 200)
        if ruta in api.cuerpo_crudo:
            cuerpo = api.cuerpo_crudo[ruta]
        elif estado == 200:
            datos = api.listings if ruta == "/listings" else api.historico
            cuerpo = json.dumps(datos).encode("utf-8")
        else:
            cuerpo = json.dumps({"detail": "error"}).encode("utf-8")
        self.send_response(estado)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)


class FakeApi:
    def __init__(self, listings=None, historico=None):
        self.listings = listings_de_ejemplo() if listings is None else listings
        self.historico = historico_de_ejemplo() if historico is None else historico
        self.estado = {}  # ruta -> código HTTP
        self.cuerpo_crudo = {}  # ruta -> bytes que se sirven tal cual
        self.retardo = 0.0
        self.peticiones = []
        self._server = None
        self._hilo = None

    @property
    def url(self):
        return f"http://127.0.0.1:{self._server.server_address[1]}"

    def start(self):
        self._server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        self._server.api = self
        self._hilo = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._hilo.start()
        return self

    def stop(self):
        if self._server:
            self._server.shutdown()
            self._server.server_close()
            self._server = None

    def __enter__(self):
        return self.start()

    def __exit__(self, *exc):
        self.stop()


def puerto_sin_servidor():
    """Un puerto en el que no escucha nadie (para probar conexión rechazada)."""
    import socket

    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]
