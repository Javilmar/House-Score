"""Traduce el formato del scraper (campos en ingles) al contrato de la API (T023, T039).

Compartido por la migracion de datos existentes y por el cliente del scraper, para que
ambos envien exactamente lo mismo.
"""

from typing import Any

_PRINCIPALES = {
    "title": "titulo",
    "price": "precio",
    "m2": "m2",
    "rooms": "habitaciones",
    "bathrooms": "banos",
    "municipio": "municipio",
    "source": "fuente",
    "score": "score",
    "datos_insuficientes": "datos_insuficientes",
    "url": "url",
}

# Estado propio del almacen antiguo (listings_store): la API lo lleva en sus propias columnas
_ESTADO_ALMACEN = {
    "first_seen",
    "last_seen",
    "status",
    "price_drop",
    "previous_price",
    "_candidate_price",
}


def payload_desde_scraper(item: dict[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {
        destino: item[origen] for origen, destino in _PRINCIPALES.items() if origen in item
    }
    payload["detalle"] = {
        k: v for k, v in item.items() if k not in _PRINCIPALES and k not in _ESTADO_ALMACEN
    }
    return payload
