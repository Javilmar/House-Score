"""Configuración leída de variables de entorno (T015)."""

import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    database_url: str
    # Migraciones por conexión directa: el pooler de Neon (PgBouncer en modo transacción)
    # no conserva estado de sesión. Sin DATABASE_URL_UNPOOLED se usa la misma que la API.
    migration_url: str
    ingest_secret: str
    rate_limit: str


def _sqlalchemy_url(url: str) -> str:
    """Neon y otros proveedores dan `postgresql://`; SQLAlchemy usaría psycopg2, que no
    está instalado. Se fija psycopg 3 sin tocar URLs que ya nombran driver."""
    for scheme in ("postgresql://", "postgres://"):
        if url.startswith(scheme):
            return "postgresql+psycopg://" + url[len(scheme) :]
    return url


@lru_cache
def get_settings() -> Settings:
    database_url = _sqlalchemy_url(os.environ.get("DATABASE_URL", "sqlite:///./housescore.db"))
    unpooled = os.environ.get("DATABASE_URL_UNPOOLED")
    return Settings(
        database_url=database_url,
        migration_url=_sqlalchemy_url(unpooled) if unpooled else database_url,
        ingest_secret=os.environ.get("INGEST_SECRET", ""),
        rate_limit=os.environ.get("RATE_LIMIT", "60/minute"),
    )
