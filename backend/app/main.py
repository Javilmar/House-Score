"""Arranque de la API de HouseScore (T016)."""

from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

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
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.include_router(routes_listings.build_router(limiter, settings.rate_limit))
    app.include_router(routes_ingest.build_router(settings))
    return app


app = create_app()
