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
    # Orígenes del front estático (Cloudflare Pages) que pueden leer la API desde el navegador.
    cors_origins: tuple[str, ...]


def _sqlalchemy_url(url: str) -> str:
    """Neon y otros proveedores dan `postgresql://`; SQLAlchemy usaría psycopg2, que no
    está instalado. Se fija psycopg 3 sin tocar URLs que ya nombran driver."""
    for scheme in ("postgresql://", "postgres://"):
        if url.startswith(scheme):
            return "postgresql+psycopg://" + url[len(scheme) :]
    return url


@lru_cache
def get_settings() -> Settings:
    bruta = os.environ.get("DATABASE_URL", "").strip()
    if not bruta:
        # Sin esto la API arrancaría sobre un SQLite vacío y serviría 0 listings sin avisar.
        raise RuntimeError(
            "Falta DATABASE_URL: define la conexión a la base de datos (en Render, la de Neon)"
        )
    database_url = _sqlalchemy_url(bruta)
    unpooled = os.environ.get("DATABASE_URL_UNPOOLED")
    return Settings(
        database_url=database_url,
        migration_url=_sqlalchemy_url(unpooled) if unpooled else database_url,
        ingest_secret=os.environ.get("INGEST_SECRET", ""),
        rate_limit=os.environ.get("RATE_LIMIT", "60/minute"),
        cors_origins=tuple(
            o.strip() for o in os.environ.get("CORS_ORIGINS", "").split(",") if o.strip()
        ),
    )
