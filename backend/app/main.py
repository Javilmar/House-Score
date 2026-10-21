"""Arranque de la API de HouseScore (T016)."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.gzip import GZipMiddleware

from app.api import routes_ingest, routes_listings
from app.core.clock import get_hoy
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.rate_limit import crear_limiter

__all__ = ["app", "create_app", "get_hoy"]


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    limiter = crear_limiter()

    app = FastAPI(title="HouseScore API")
    # Añadido antes que CORS (el último añadido es el más externo): CORS envuelve a gzip.
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_methods=["GET"],
        allow_credentials=False,
    )
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.include_router(routes_listings.build_router(limiter, settings.rate_limit))
    app.include_router(routes_ingest.build_router(settings))
    return app


app = create_app()
