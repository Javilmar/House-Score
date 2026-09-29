from datetime import date

from sqlalchemy import Date, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PasadaDiaria(Base):
    """Agregados de un día: equivale a una fila de historico_diario.json (FR-013)."""

    __tablename__ = "pasada_diaria"

    fecha: Mapped[date] = mapped_column(Date, primary_key=True)
    total_listings: Mapped[int] = mapped_column(Integer)
    score_medio: Mapped[float | None] = mapped_column(Float)
    precio_medio: Mapped[int | None] = mapped_column(Integer)
    precio_min: Mapped[int | None] = mapped_column(Integer)
    precio_max: Mapped[int | None] = mapped_column(Integer)
