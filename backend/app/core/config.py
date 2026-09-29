"""Configuración leída de variables de entorno (T015)."""

import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    database_url: str
    ingest_secret: str
    rate_limit: str


@lru_cache
def get_settings() -> Settings:
    return Settings(
        database_url=os.environ.get("DATABASE_URL", "sqlite:///./housescore.db"),
        ingest_secret=os.environ.get("INGEST_SECRET", ""),
        rate_limit=os.environ.get("RATE_LIMIT", "60/minute"),
    )
