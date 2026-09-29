from datetime import datetime

from sqlalchemy import DateTime, Float, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PrecioReferencia(Base):
    """Mediana de €/m² por municipio (equivale a config/precios_referencia.json)."""

    __tablename__ = "precio_referencia"

    municipio: Mapped[str] = mapped_column(String(128), primary_key=True)
    mediana_eur_m2: Mapped[float] = mapped_column(Float)
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
