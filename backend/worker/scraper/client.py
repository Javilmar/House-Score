"""Cliente del scraper: envia una pasada completa a POST /ingest (T039).

Sustituye a guardar.py + `git push`. La ingesta es idempotente por `url`, asi que reintentar
tras un corte de red es seguro.

Uso como CLI (desde backend/):
    INGEST_SECRET=... python -m worker.scraper.client last_property_data.json
Uso desde el scorer:
    from worker.scraper.client import enviar_pasada
    enviar_pasada(listings, secreto)
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import httpx

from app.services.formato_scraper import payload_desde_scraper

API_URL_DEFECTO = "http://localhost:8000"
_TIMEOUT = 120.0


class IngestError(RuntimeError):
    """La pasada no pudo guardarse en la API."""


def enviar_pasada(
    items: list[dict],
    secreto: str,
    *,
    api_url: str = API_URL_DEFECTO,
    http: httpx.Client | None = None,
    reintentos: int = 3,
    espera: float = 2.0,
) -> dict:
    cuerpo = {"listings": [payload_desde_scraper(i) for i in items if i.get("url")]}
    cabeceras = {"Authorization": f"Bearer {secreto}"}
    propio = http is None
    cliente = http or httpx.Client(base_url=api_url, timeout=_TIMEOUT)
    try:
        ultimo = "sin intentos"
        for intento in range(reintentos):
            if intento:
                time.sleep(espera * 2 ** (intento - 1))
            try:
                r = cliente.post("/ingest", json=cuerpo, headers=cabeceras)
            except httpx.TransportError as e:
                ultimo = f"error de conexion: {e}"
                continue
            if r.status_code == 201:
                return r.json()
            ultimo = f"HTTP {r.status_code}"
            if r.status_code < 500 and r.status_code != 429:
                raise IngestError(f"la API rechazo la pasada: {ultimo}")
        raise IngestError(f"no se pudo guardar la pasada tras {reintentos} intentos: {ultimo}")
    finally:
        if propio:
            cliente.close()


def main(argv: list[str] | None = None, http: httpx.Client | None = None) -> int:
    parser = argparse.ArgumentParser(description="Envia una pasada del scraper a la API")
    parser.add_argument("archivo", type=Path, help="JSON con la lista de listings del scorer")
    parser.add_argument("--api-url", default=os.environ.get("HOUSESCORE_API_URL", API_URL_DEFECTO))
    args = parser.parse_args(argv)

    secreto = os.environ.get("INGEST_SECRET", "")
    if not secreto:
        print("Error: define la variable de entorno INGEST_SECRET", file=sys.stderr)
        return 2
    try:
        items = json.loads(args.archivo.read_text(encoding="utf-8"))
        resumen = enviar_pasada(items, secreto, api_url=args.api_url, http=http)
    except (OSError, ValueError, IngestError) as e:
        print(f"Error al enviar la pasada: {e}", file=sys.stderr)
        return 1
    print("Pasada guardada:", json.dumps(resumen, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
