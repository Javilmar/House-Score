"""Conexion del scorer con la API (T038/T040): sustituye al git push y a frontend/datos.

- `verificar_api`: comprobacion previa, para no scrapear varios minutos con la API caida.
- `cargar_historial_api`: historial (first_seen y ultimo precio) que el scorer necesita para
  puntuar dias en el mercado y bajadas de precio; antes salia de frontend/datos/*.json.
- `publicar_pasada`: envia el lote a POST /ingest. Si falla, guarda una copia para reenviarla
  con `python -m worker.scraper.client <fichero>` en vez de perder el lote.
"""

import json
import os
from datetime import date
from pathlib import Path

import httpx

from worker.scraper.client import API_URL_DEFECTO, IngestError, enviar_pasada


def _api_url(api_url: str | None) -> str:
    return api_url or os.environ.get("HOUSESCORE_API_URL", API_URL_DEFECTO)


def directorio_pendientes() -> Path:
    base = Path(os.environ.get("HERMES_DATA_DIR", Path.home() / "AppData/Local/hermes"))
    return base / "pendientes"


def _cliente(api_url: str | None, http: httpx.Client | None) -> tuple[httpx.Client, bool]:
    if http is not None:
        return http, False
    return httpx.Client(base_url=_api_url(api_url), timeout=60.0), True


def _get_listings(params: dict, api_url: str | None, http: httpx.Client | None) -> list[dict]:
    cliente, propio = _cliente(api_url, http)
    try:
        r = cliente.get("/listings", params=params)
        r.raise_for_status()
        return r.json()
    finally:
        if propio:
            cliente.close()


def verificar_api(*, api_url: str | None = None, http: httpx.Client | None = None) -> None:
    try:
        _get_listings({"municipio": "__comprobacion__"}, api_url, http)
    except (httpx.HTTPError, ValueError) as e:
        raise IngestError(f"la API no responde en {_api_url(api_url)}: {e}") from e


def cargar_historial_api(
    *, api_url: str | None = None, http: httpx.Client | None = None
) -> dict[str, dict]:
    """Devuelve {url: {"first_seen", "price"}}, el formato que espera assign_market_fields."""
    try:
        listings = _get_listings({"incluir_retirados": "true"}, api_url, http)
    except (httpx.HTTPError, ValueError) as e:
        raise IngestError(f"no se pudo cargar el historial desde la API: {e}") from e
    return {
        li["url"]: {"first_seen": li["primera_aparicion"], "price": li["precio"]} for li in listings
    }


def _guardar_pendiente(items: list[dict], lote: str, fecha: date, pendientes: Path | None) -> Path:
    carpeta = pendientes or directorio_pendientes()
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / f"{fecha.isoformat()}-{lote}.json"
    ruta.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    return ruta


def publicar_pasada(
    items: list[dict],
    lote: str,
    *,
    fecha: date | None = None,
    api_url: str | None = None,
    http: httpx.Client | None = None,
    secreto: str | None = None,
    pendientes: Path | None = None,
    reintentos: int = 3,
    espera: float = 2.0,
) -> dict:
    fecha = fecha or date.today()
    secreto = secreto if secreto is not None else os.environ.get("INGEST_SECRET", "")
    if not secreto:
        ruta = _guardar_pendiente(items, lote, fecha, pendientes)
        raise IngestError(f"falta INGEST_SECRET; el lote queda guardado en {ruta}")
    try:
        return enviar_pasada(
            items,
            secreto,
            api_url=_api_url(api_url),
            http=http,
            reintentos=reintentos,
            espera=espera,
        )
    except IngestError as e:
        ruta = _guardar_pendiente(items, lote, fecha, pendientes)
        raise IngestError(f"{e}; el lote queda guardado en {ruta} para reenviarlo") from e
