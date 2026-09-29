from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class ListingIn(BaseModel):
    """Un listing tal como lo envia el scraper a POST /ingest."""

    url: str = Field(min_length=1)
    titulo: str = ""
    precio: int | float | None = None
    m2: int | float | None = None
    habitaciones: int | float | None = None
    banos: int | float | None = None
    municipio: str | None = None
    fuente: str = ""
    score: float | None = None
    datos_insuficientes: bool = False
    detalle: dict = Field(default_factory=dict)


class PasadaIn(BaseModel):
    listings: list[ListingIn]


class ResumenPasada(BaseModel):
    listings_procesados: int
    nuevos: int
    actualizados: int
    descartados_bloqueados: int
    retirados: int


class ListingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    url: str
    titulo: str
    precio: int | None
    m2: int | None
    habitaciones: int | None
    banos: int | None
    municipio: str
    fuente: str
    score: float | None
    datos_insuficientes: bool
    estado: str
    primera_aparicion: date
    ultima_aparicion: date
    precio_anterior: int | None
    bajada_precio: int | None
    detalle: dict


class PasadaDiariaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    fecha: date
    total_listings: int
    score_medio: float | None
    precio_medio: int | None
    precio_min: int | None
    precio_max: int | None
