from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

ESTADO_ACTIVO = "activo"
ESTADO_RETIRADO = "retirado"


class Listing(Base):
    """Piso scrapeado, en su estado más reciente conocido (data-model.md § Listing)."""

    __tablename__ = "listing"

    id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str] = mapped_column(String(1024), unique=True, index=True)
    titulo: Mapped[str] = mapped_column(String(512), default="")
    precio: Mapped[int | None] = mapped_column(Integer)  # euros enteros (FR-017)
    m2: Mapped[int | None] = mapped_column(Integer)
    habitaciones: Mapped[int | None] = mapped_column(Integer)
    banos: Mapped[int | None] = mapped_column(Integer)
    municipio: Mapped[str] = mapped_column(String(128), index=True)
    fuente: Mapped[str] = mapped_column(String(64), default="")
    score: Mapped[float | None] = mapped_column(Float)
    datos_insuficientes: Mapped[bool] = mapped_column(Boolean, default=False)
    estado: Mapped[str] = mapped_column(String(16), default=ESTADO_ACTIVO, index=True)
    primera_aparicion: Mapped[date] = mapped_column(Date)
    ultima_aparicion: Mapped[date] = mapped_column(Date)

    # Estado de la regla de bajada de precio (equivale a price_drop / previous_price /
    # _candidate_price de listings_store.py)
    precio_anterior: Mapped[int | None] = mapped_column(Integer)
    bajada_precio: Mapped[int | None] = mapped_column(Integer)
    precio_candidato: Mapped[int | None] = mapped_column(Integer)

    # Resto de campos que hoy usa el dashboard (score_details, description, eur_m2, ...)
    detalle: Mapped[dict] = mapped_column(JSON, default=dict)

    creado_en: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
