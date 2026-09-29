"""GET /listings y GET /historico: lectura publica con rate limiting por IP (T020-T022)."""

from datetime import date

from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.models import ESTADO_ACTIVO, Listing, PasadaDiaria
from app.schemas import ListingOut, PasadaDiariaOut


def build_router(limiter: Limiter, rate_limit: str) -> APIRouter:
    router = APIRouter()

    @router.get("/listings", response_model=list[ListingOut])
    @limiter.limit(rate_limit)
    def listar_listings(
        request: Request,
        municipio: str | None = None,
        incluir_retirados: bool = False,
        session: Session = Depends(get_session),
    ):
        consulta = select(Listing)
        if municipio:
            consulta = consulta.where(Listing.municipio == municipio)
        if not incluir_retirados:
            consulta = consulta.where(Listing.estado == ESTADO_ACTIVO)
        consulta = consulta.order_by(Listing.score.is_(None), Listing.score.desc(), Listing.id)
        return session.scalars(consulta).all()

    @router.get("/historico", response_model=list[PasadaDiariaOut])
    @limiter.limit(rate_limit)
    def historico(
        request: Request,
        desde: date | None = None,
        hasta: date | None = None,
        session: Session = Depends(get_session),
    ):
        consulta = select(PasadaDiaria)
        if desde:
            consulta = consulta.where(PasadaDiaria.fecha >= desde)
        if hasta:
            consulta = consulta.where(PasadaDiaria.fecha <= hasta)
        return session.scalars(consulta.order_by(PasadaDiaria.fecha)).all()

    return router
