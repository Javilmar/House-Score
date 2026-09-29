"""Reglas de negocio puras migradas de frontend/dashboard/listings_store.py y guardar.py.

Sin acceso a base de datos: se testean de forma aislada (Principio IV).
"""

import unicodedata
from dataclasses import dataclass
from typing import Any

# nuevo_precio / precio_anterior por debajo de esto = bajada >40%, sospechosa (listings_store)
OUTLIER_DROP_RATIO = 0.6
DELISTED_THRESHOLD_DAYS = 7

# Municipios de Toledo Norte descartados (guardar._TOLEDO_NORTE_BLOQUEADOS)
MUNICIPIOS_BLOQUEADOS = frozenset(
    {
        "yuncos",
        "yuncler",
        "yunclillos",
        "cedillo",
        "el viso de san juan",
        "viso de san juan",
        "carranque",
        "recas",
        "lominchar",
        "alameda de la sagra",
        "cabanas de la sagra",
        "villaluenga",
        "anover de tajo",
        "casarrubios",
        "valmojado",
        "magan",
        "cobeja",
        "numancia",
        "pantoja",
        "chozas de canales",
        "bargas",
        "mocejon",
        "burguillos",
        "cobisa",
        "olias",
    }
)


def _sin_acentos(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s))
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def esta_bloqueado(municipio: str | None) -> bool:
    """True si el municipio pertenece a la lista de descartados.

    Los datos del scraper llevan el municipio como id (`cabanas_de_la_sagra`), mientras que
    la lista usa espacios; se normaliza para que ambos formatos coincidan.
    """
    norm = _sin_acentos(municipio or "").replace("_", " ").strip()
    return norm in MUNICIPIOS_BLOQUEADOS


def _entero(valor: Any) -> int | None:
    if valor is None or valor == "":
        return None
    return int(round(float(valor)))


def normalizar_listing(d: dict[str, Any]) -> dict[str, Any]:
    """Aplica FR-005: sin m2 fiables => datos_insuficientes y sin score.

    Los JSON actuales representan "sin m2" como 0, y el scorer puede marcar
    `datos_insuficientes` aunque haya m2; en ambos casos no se sirve un score forzado
    (Principio I de la constitucion).
    """
    m2 = _entero(d.get("m2")) or None  # 0 => ausente
    insuficientes = bool(d.get("datos_insuficientes")) or m2 is None
    score = d.get("score")
    return {
        "url": d["url"],
        "titulo": d.get("titulo") or "",
        "precio": _entero(d.get("precio")) or None,
        "m2": m2,
        "habitaciones": _entero(d.get("habitaciones")),
        "banos": _entero(d.get("banos")),
        "municipio": (d.get("municipio") or "").strip() or "desconocido",
        "fuente": d.get("fuente") or "",
        "score": None if insuficientes or score is None else float(score),
        "datos_insuficientes": insuficientes,
        "detalle": d.get("detalle") or {},
    }


@dataclass(frozen=True)
class EstadoPrecio:
    precio: int | None
    anterior: int | None = None
    bajada: int | None = None
    candidato: int | None = None


@dataclass(frozen=True)
class ResultadoPrecio:
    estado: EstadoPrecio
    bajada_confirmada: bool


def aplicar_precio(viejo: EstadoPrecio, nuevo: int | None) -> ResultadoPrecio:
    """Decide precio / bajada / candidato (equivale a listings_store._aplicar_precio).

    La bajada se recalcula contra el ultimo precio visto en cada pasada, sin arrastrar
    marcas antiguas. Un salto a la baja de mas del 40% en una sola pasada no se acepta
    hasta confirmarse con un valor igual en la pasada siguiente.
    """
    if nuevo is None:
        return ResultadoPrecio(viejo, False)

    if not viejo.precio or nuevo >= viejo.precio:
        return ResultadoPrecio(EstadoPrecio(precio=nuevo), False)

    es_salto_grande = (nuevo / viejo.precio) < OUTLIER_DROP_RATIO
    confirmado = viejo.candidato == nuevo

    if es_salto_grande and not confirmado:
        return ResultadoPrecio(
            EstadoPrecio(
                precio=viejo.precio,
                anterior=viejo.anterior,
                bajada=viejo.bajada,
                candidato=nuevo,
            ),
            False,
        )

    return ResultadoPrecio(
        EstadoPrecio(precio=nuevo, anterior=viejo.precio, bajada=viejo.precio - nuevo),
        True,
    )
