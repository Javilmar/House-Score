"""Migracion one-off de frontend/datos y frontend/config a la base de datos (T023, SC-004).

1. Carga `listings.json` como estado base (fechas, estado y marcas de precio intactas).
2. Carga `historico_diario.json` como agregados diarios.
3. Repite, en orden, las pasadas diarias `YYYY-MM-DD.json` posteriores al estado base a
   traves de la misma logica de ingesta, porque `listings.json` puede ir por detras de
   las pasadas mas recientes.
4. Carga los precios de referencia por municipio.
Todo en una unica transaccion: si algo falla no queda nada a medias.
"""

import json
import re
from datetime import date
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    ESTADO_ACTIVO,
    ESTADO_RETIRADO,
    HistorialPrecio,
    Listing,
    PasadaDiaria,
    PrecioReferencia,
)
from app.schemas import ListingIn
from app.services.formato_scraper import payload_desde_scraper
from app.services.ingest_service import procesar_pasada
from app.services.reglas import normalizar_listing

_PASADA = re.compile(r"^(\d{4}-\d{2}-\d{2})\.json$")


class BaseDeDatosNoVacia(RuntimeError):
    """La migracion solo se ejecuta sobre una base de datos sin listings."""


def _fecha(valor: str | None, defecto: date) -> date:
    return date.fromisoformat(valor) if valor else defecto


def migrar(session: Session, datos_dir: Path, config_dir: Path) -> dict:
    listings_path = Path(datos_dir) / "listings.json"
    if not listings_path.exists():
        raise FileNotFoundError(listings_path)
    if session.scalar(select(func.count()).select_from(Listing)):
        raise BaseDeDatosNoVacia("la base de datos ya contiene listings")

    try:
        resumen = _migrar(session, Path(datos_dir), Path(config_dir), listings_path)
        session.commit()
        return resumen
    except Exception:
        session.rollback()
        raise


def _migrar(session: Session, datos_dir: Path, config_dir: Path, listings_path: Path) -> dict:
    items = json.loads(listings_path.read_text(encoding="utf-8"))

    vistos: dict[str, dict] = {}
    for item in items:
        if item.get("url"):
            vistos[item["url"]] = item

    ultima_vista = max(
        (date.fromisoformat(i["last_seen"]) for i in vistos.values() if i.get("last_seen")),
        default=date.min,
    )
    hoy = date.today()
    pares: list[tuple[Listing, dict]] = []
    for item in vistos.values():
        d = normalizar_listing(payload_desde_scraper(item))
        primera = _fecha(item.get("first_seen"), hoy)
        ultima = _fecha(item.get("last_seen"), primera)
        listing = Listing(
            **d,
            estado=ESTADO_RETIRADO if item.get("status") == "delisted" else ESTADO_ACTIVO,
            primera_aparicion=primera,
            ultima_aparicion=ultima,
            precio_anterior=item.get("previous_price"),
            bajada_precio=item.get("price_drop"),
            precio_candidato=item.get("_candidate_price"),
        )
        session.add(listing)
        pares.append((listing, item))
    session.flush()

    for listing, item in pares:
        if item.get("previous_price") and item.get("price_drop") and listing.precio:
            session.add(
                HistorialPrecio(
                    listing_id=listing.id,
                    precio_anterior=item["previous_price"],
                    precio_nuevo=listing.precio,
                    fecha_cambio=listing.ultima_aparicion,
                )
            )

    historico_path = datos_dir / "historico_diario.json"
    filas = (
        json.loads(historico_path.read_text(encoding="utf-8")) if historico_path.exists() else []
    )
    for fila in filas:
        session.add(
            PasadaDiaria(
                fecha=date.fromisoformat(fila["fecha"]),
                total_listings=fila["count"],
                precio_medio=fila.get("avg_price"),
                score_medio=fila.get("avg_score"),
                precio_min=fila.get("min_price"),
                precio_max=fila.get("max_price"),
            )
        )
    session.flush()

    repetidas: list[str] = []
    pasadas = sorted((m.group(1), p) for p in datos_dir.iterdir() if (m := _PASADA.match(p.name)))
    for fecha_txt, ruta in pasadas:
        fecha = date.fromisoformat(fecha_txt)
        if fecha <= ultima_vista:
            continue
        crudos = json.loads(ruta.read_text(encoding="utf-8"))
        procesar_pasada(
            session,
            [ListingIn(**payload_desde_scraper(c)) for c in crudos if c.get("url")],
            fecha,
        )
        repetidas.append(fecha_txt)

    return {
        "listings_base": len(vistos),
        "historico": len(filas),
        "pasadas_repetidas": repetidas,
        "precios_referencia": _migrar_precios_referencia(session, config_dir),
    }


def _migrar_precios_referencia(session: Session, config_dir: Path) -> int:
    ruta = config_dir / "precios_referencia.json"
    if not ruta.exists():
        return 0
    municipios = json.loads(ruta.read_text(encoding="utf-8")).get("municipios", {})
    for nombre, datos in municipios.items():
        session.add(PrecioReferencia(municipio=nombre, mediana_eur_m2=float(datos["eur_m2"])))
    return len(municipios)
