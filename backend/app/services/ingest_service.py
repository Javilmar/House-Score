"""Ingesta de una pasada del scraper (T031-T035, T037).

Toda la pasada se guarda en una unica transaccion: quien lee ve la pasada anterior completa
o la nueva completa, nunca una mezcla (edge case del spec). Las pasadas se serializan con un
lock para que dos ejecuciones casi simultaneas no dupliquen listings.
"""

import logging
import threading
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import ESTADO_ACTIVO, ESTADO_RETIRADO, HistorialPrecio, Listing, PasadaDiaria
from app.schemas import ListingIn, ResumenPasada
from app.services.reglas import (
    DELISTED_THRESHOLD_DAYS,
    EstadoPrecio,
    aplicar_precio,
    esta_bloqueado,
    normalizar_listing,
)

logger = logging.getLogger("housescore.ingest")
_lock = threading.Lock()
_CHUNK = 500


def ingest_pasada(session: Session, items: list[ListingIn], hoy: date) -> ResumenPasada:
    with _lock:
        try:
            resumen = procesar_pasada(session, items, hoy)
            session.commit()
            return resumen
        except Exception:
            session.rollback()
            logger.exception(
                "ingesta fallida",
                extra={"contexto": {"fecha": hoy.isoformat(), "listings": len(items)}},
            )
            raise


def procesar_pasada(session: Session, items: list[ListingIn], hoy: date) -> ResumenPasada:
    """Aplica una pasada sin hacer commit (lo usa tambien la migracion de datos)."""
    normalizados: dict[str, dict] = {}
    bloqueados = 0
    for item in items:
        d = normalizar_listing(item.model_dump())
        if esta_bloqueado(d["municipio"]):
            bloqueados += 1
            continue
        normalizados[d["url"]] = d  # url repetida en la pasada: gana la ultima

    existentes = _cargar_existentes(session, list(normalizados))
    nuevos = actualizados = 0
    for url, d in normalizados.items():
        listing = existentes.get(url)
        if listing is None:
            session.add(_nuevo_listing(d, hoy))
            nuevos += 1
        else:
            _actualizar_listing(session, listing, d, hoy)
            actualizados += 1
    session.flush()

    retirados = _marcar_retirados(session, hoy)
    actualizar_pasada_diaria(session, hoy)
    return ResumenPasada(
        listings_procesados=len(normalizados),
        nuevos=nuevos,
        actualizados=actualizados,
        descartados_bloqueados=bloqueados,
        retirados=retirados,
    )


def _cargar_existentes(session: Session, urls: list[str]) -> dict[str, Listing]:
    encontrados: dict[str, Listing] = {}
    for i in range(0, len(urls), _CHUNK):
        chunk = urls[i : i + _CHUNK]
        for listing in session.scalars(select(Listing).where(Listing.url.in_(chunk))):
            encontrados[listing.url] = listing
    return encontrados


def _nuevo_listing(d: dict, hoy: date) -> Listing:
    return Listing(
        **d,
        estado=ESTADO_ACTIVO,
        primera_aparicion=hoy,
        ultima_aparicion=hoy,
    )


def _actualizar_listing(session: Session, listing: Listing, d: dict, hoy: date) -> None:
    viejo = EstadoPrecio(
        precio=listing.precio,
        anterior=listing.precio_anterior,
        bajada=listing.bajada_precio,
        candidato=listing.precio_candidato,
    )
    nuevo_precio = d["precio"]
    # Reintento de la misma pasada el mismo dia (ver edge cases): no debe confirmar una
    # bajada candidata ni borrar la marca de bajada ya registrada.
    es_reintento = listing.ultima_aparicion == hoy and nuevo_precio in (
        viejo.precio,
        viejo.candidato,
    )
    if es_reintento:
        resultado_estado, confirmada = viejo, False
    else:
        r = aplicar_precio(viejo, nuevo_precio)
        resultado_estado, confirmada = r.estado, r.bajada_confirmada

    if confirmada:
        session.add(
            HistorialPrecio(
                listing_id=listing.id,
                precio_anterior=resultado_estado.anterior,
                precio_nuevo=resultado_estado.precio,
                fecha_cambio=hoy,
            )
        )

    listing.titulo = d["titulo"]
    listing.m2 = d["m2"]
    listing.habitaciones = d["habitaciones"]
    listing.banos = d["banos"]
    listing.municipio = d["municipio"]
    listing.fuente = d["fuente"]
    listing.score = d["score"]
    listing.datos_insuficientes = d["datos_insuficientes"]
    listing.detalle = d["detalle"]
    listing.precio = resultado_estado.precio
    listing.precio_anterior = resultado_estado.anterior
    listing.bajada_precio = resultado_estado.bajada
    listing.precio_candidato = resultado_estado.candidato
    listing.ultima_aparicion = hoy
    listing.estado = ESTADO_ACTIVO


def _marcar_retirados(session: Session, hoy: date) -> int:
    limite = hoy - timedelta(days=DELISTED_THRESHOLD_DAYS)
    candidatos = session.scalars(
        select(Listing).where(Listing.estado == ESTADO_ACTIVO, Listing.ultima_aparicion <= limite)
    ).all()
    for listing in candidatos:
        listing.estado = ESTADO_RETIRADO
    return len(candidatos)


def actualizar_pasada_diaria(session: Session, hoy: date) -> None:
    """Agregados del dia sobre los listings activos (append_daily_aggregate)."""
    session.flush()
    total, precio_medio, score_medio, pmin, pmax = session.execute(
        select(
            func.count(Listing.id),
            func.avg(Listing.precio),
            func.avg(Listing.score),
            func.min(Listing.precio),
            func.max(Listing.precio),
        ).where(Listing.estado == ESTADO_ACTIVO)
    ).one()
    fila = session.get(PasadaDiaria, hoy)
    if fila is None:
        fila = PasadaDiaria(fecha=hoy)
        session.add(fila)
    fila.total_listings = total
    fila.precio_medio = round(precio_medio) if precio_medio is not None else None
    fila.score_medio = round(score_medio, 2) if score_medio is not None else None
    fila.precio_min = pmin
    fila.precio_max = pmax
