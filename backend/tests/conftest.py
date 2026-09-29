import os

# Los tests nunca deben tocar la base de datos real: se fuerza una URL de memoria
# antes de importar la app, y cada test crea su propio engine (TEST_DATABASE_URL opcional).
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["INGEST_SECRET"] = "test-secret"
os.environ["RATE_LIMIT"] = "1000/minute"

from datetime import date  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

import app.models  # noqa: E402, F401
from app.core.config import get_settings  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import get_session  # noqa: E402
from app.main import create_app, get_hoy  # noqa: E402

HOY = date(2026, 9, 29)
AUTH = {"Authorization": "Bearer test-secret"}


@pytest.fixture
def engine():
    url = os.environ.get("TEST_DATABASE_URL", "sqlite://")
    if url.startswith("sqlite"):
        eng = create_engine(url, poolclass=StaticPool, connect_args={"check_same_thread": False})
    else:
        eng = create_engine(url)
    Base.metadata.drop_all(eng)
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture
def session(engine):
    with sessionmaker(bind=engine, expire_on_commit=False)() as s:
        yield s


@pytest.fixture
def hoy():
    """Fecha de hoy que ve la API; los tests la mueven con hoy["fecha"] = ..."""
    return {"fecha": HOY}


@pytest.fixture
def make_client(engine, hoy):
    """Fabrica de clientes; permite fijar variables de entorno antes de crear la app."""

    def _make(**env):
        old = {k: os.environ.get(k) for k in env}
        os.environ.update(env)
        get_settings.cache_clear()
        try:
            app = create_app()
        finally:
            for k, v in old.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
            get_settings.cache_clear()
        maker = sessionmaker(bind=engine, expire_on_commit=False)

        def _session():
            with maker() as s:
                yield s

        app.dependency_overrides[get_session] = _session
        app.dependency_overrides[get_hoy] = lambda: hoy["fecha"]
        return TestClient(app)

    return _make


@pytest.fixture
def client(make_client):
    return make_client()
