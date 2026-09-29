"""Cliente de la API de HouseScore para el dashboard (spec 002).

Traduce el contrato de la API (specs/001-backend-api-bbdd/contracts/api.md) a las columnas que
ya usa app.py. Contrato del módulo: specs/002-front-consume-api/contracts/api-datos.md.
"""

import copy
import os

import pandas as pd
import requests

# 127.0.0.1 y no "localhost": en Windows "localhost" prueba antes ::1 y cada petición pierde ~2 s
# (la API solo escucha en IPv4). Medido: 2,06 s con localhost frente a 0,01 s con 127.0.0.1.
API_URL_DEFECTO = "http://127.0.0.1:8000"
_TIMEOUT = (3, 15)  # conexión, lectura (segundos)

# Campo de la API -> columna que usa app.py
_PRINCIPALES = {
    "titulo": "title",
    "precio": "price",
    "m2": "m2",
    "habitaciones": "rooms",
    "banos": "bathrooms",
    "url": "url",
    "fuente": "source",
    "municipio": "municipio",
    "score": "score",
    "datos_insuficientes": "datos_insuficientes",
    "primera_aparicion": "first_seen",
    "ultima_aparicion": "last_seen",
    "bajada_precio": "price_drop",
    "precio_anterior": "previous_price",
}
_ESTADOS = {"activo": "active", "retirado": "delisted"}

# Los datos antiguos siempre traían estos campos; si el detalle de la API viene vacío o
# incompleto se rellenan con un valor neutro para que el resto de app.py no tenga que
# tratar tipos distintos (texto, lista, dict) según el listing.
_DEFECTOS_DETALLE = {
    "location": "",
    "description": "",
    "floor": "",
    "conservation": "",
    "energy_rating": "",
    "pisos_id": "",
    "features": [],
    "detail_features": {},
    "score_details": [],
    "exterior": False,
    "cumple_requisitos": True,
    "year_built": 0,
}

# Los JSON antiguos escribían 0 cuando faltaba precio, m², habitaciones, baños o score
# (`prop.get("...", 0)` en el scorer) y app.py hace int(...) sobre ellos sin comprobar NaN.
# La API los sirve como null; aquí se traducen igual que antes para no tocar el resto de app.py.
# La marca real de "sin valorar" sigue siendo `datos_insuficientes`.
_CERO_SI_FALTA = ["price", "m2", "rooms", "bathrooms", "score"]
_NUMERICAS = ["price", "m2", "rooms", "bathrooms", "score", "year_built", "price_drop", "previous_price"]

_HISTORICO = {
    "total_listings": "count",
    "score_medio": "avg_score",
    "precio_medio": "avg_price",
    "precio_min": "min_price",
    "precio_max": "max_price",
}


class ApiNoDisponible(Exception):
    """La API no se puede usar: conexión, tiempo agotado, error HTTP o cuerpo no válido."""

    def __init__(self, mensaje, url):
        super().__init__(f"{mensaje} ({url})")
        self.mensaje = mensaje
        self.url = url


def url_api(api_url=None):
    """Dirección de la API: argumento, o HOUSESCORE_API_URL, o la local por defecto.

    Se lee en cada llamada (no al importar) para poder cambiarla sin reiniciar.
    """
    return (api_url or os.environ.get("HOUSESCORE_API_URL") or API_URL_DEFECTO).rstrip("/")


def listings_a_dataframe(items):
    """Contrato de /listings -> DataFrame con las columnas de app.py (data-model.md)."""
    if not items:
        return pd.DataFrame()

    filas = []
    for item in items:
        fila = dict(item.get("detalle") or {})
        fila.pop("eur_m2", None)  # se recalcula abajo, como hacía cargar_datos()
        for clave, defecto in _DEFECTOS_DETALLE.items():
            if fila.get(clave) is None:
                fila[clave] = copy.deepcopy(defecto)
        for origen, destino in _PRINCIPALES.items():
            fila[destino] = item.get(origen)  # una clave del detalle nunca pisa una principal
        fila["status"] = _ESTADOS.get(item.get("estado"), item.get("estado"))
        filas.append(fila)

    df = pd.DataFrame(filas)
    for col in _NUMERICAS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in _CERO_SI_FALTA:
        df[col] = df[col].fillna(0)
    df["first_seen"] = pd.to_datetime(df["first_seen"], errors="coerce")
    df["last_seen"] = pd.to_datetime(df["last_seen"], errors="coerce")
    # m² = 0 no es un dato fiable: NaN (app.py protege con pd.notna; inf reventaba int())
    df["eur_m2"] = (df["price"] / df["m2"].where(df["m2"] > 0)).round(0)
    return df.sort_values("score", ascending=False, na_position="last")


def historico_a_dataframe(filas):
    """Contrato de /historico -> DataFrame con las columnas de app.py (data-model.md)."""
    if not filas:
        return pd.DataFrame()

    df = pd.DataFrame(filas).rename(columns=_HISTORICO)
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    for col in _HISTORICO.values():
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.sort_values("fecha")


def _pedir(ruta, api_url, params=None):
    """GET a la API. Una sola petición, sin reintentos; cualquier fallo -> ApiNoDisponible."""
    url = f"{url_api(api_url)}{ruta}"
    try:
        respuesta = requests.get(url, params=params, timeout=_TIMEOUT)
    except requests.exceptions.Timeout as e:
        raise ApiNoDisponible("La API no ha respondido a tiempo", url) from e
    except requests.exceptions.RequestException as e:
        raise ApiNoDisponible("No se puede conectar con la API", url) from e

    if respuesta.status_code == 429:
        raise ApiNoDisponible(
            "La API ha limitado las peticiones; espera un momento y recarga", url
        )
    if respuesta.status_code != 200:
        raise ApiNoDisponible(f"La API ha devuelto un error (HTTP {respuesta.status_code})", url)

    try:
        datos = respuesta.json()
    except ValueError as e:
        raise ApiNoDisponible("La respuesta de la API no es válida", url) from e
    if not isinstance(datos, list) or not all(isinstance(x, dict) for x in datos):
        raise ApiNoDisponible("La respuesta de la API no es válida", url)
    return datos


def obtener_listings(api_url=None):
    return listings_a_dataframe(_pedir("/listings", api_url, {"incluir_retirados": "true"}))


def obtener_historico(api_url=None):
    return historico_a_dataframe(_pedir("/historico", api_url))
