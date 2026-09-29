"""POST /ingest: escritura de una pasada del scraper (T030, T036).

No es publico: el tunel no enruta esta ruta (FR-011) y ademas exige el secreto compartido.
"""

import hmac
import logging
from datetime import date

from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.clock import get_hoy
from app.core.config import Settings
from app.db.session import get_session
from app.schemas import PasadaIn, ResumenPasada
from app.services.ingest_service import ingest_pasada

logger = logging.getLogger("housescore.ingest")


def build_router(settings: Settings) -> APIRouter:
    router = APIRouter()

    def exigir_secreto(authorization: str | None = Header(default=None)) -> None:
        esquema, _, token = (authorization or "").partition(" ")
        valido = (
            bool(settings.ingest_secret)
            and esquema == "Bearer"
            and hmac.compare_digest(token.encode(), settings.ingest_secret.encode())
        )
        if not valido:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "no autorizado")

    @router.post(
        "/ingest",
        response_model=ResumenPasada,
        status_code=status.HTTP_201_CREATED,
        dependencies=[Depends(exigir_secreto)],
    )
    def ingest(
        pasada: PasadaIn,
        session: Session = Depends(get_session),
        hoy: date = Depends(get_hoy),
    ):
        try:
            return ingest_pasada(session, pasada.listings, hoy)
        except Exception:
            # el detalle ya esta en el log (FR-014); al cliente solo un error generico
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "error al guardar la pasada"},
            )

    return router
