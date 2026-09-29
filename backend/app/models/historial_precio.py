from datetime import date

from sqlalchemy import Date, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class HistorialPrecio(Base):
    """Cada bajada de precio confirmada de un listing (FR-004)."""

    __tablename__ = "historial_precio"

    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(
        ForeignKey("listing.id", ondelete="CASCADE"), index=True
    )
    precio_anterior: Mapped[int] = mapped_column(Integer)
    precio_nuevo: Mapped[int] = mapped_column(Integer)
    fecha_cambio: Mapped[date] = mapped_column(Date)
