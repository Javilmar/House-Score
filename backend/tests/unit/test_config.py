import pytest

from app.core.config import get_settings


def test_sin_database_url_la_api_no_arranca(monkeypatch):
    # Antes caía en un SQLite vacío dentro del contenedor y la API servía 0 listings sin avisar.
    monkeypatch.delenv("DATABASE_URL", raising=False)
    get_settings.cache_clear()
    try:
        with pytest.raises(RuntimeError, match="DATABASE_URL"):
            get_settings()
    finally:
        get_settings.cache_clear()


def test_database_url_vacia_cuenta_como_ausente(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "  ")
    get_settings.cache_clear()
    try:
        with pytest.raises(RuntimeError, match="DATABASE_URL"):
            get_settings()
    finally:
        get_settings.cache_clear()
