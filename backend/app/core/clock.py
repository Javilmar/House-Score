from datetime import date


def get_hoy() -> date:
    """Fecha de la pasada. Dependencia de FastAPI para poder fijarla en tests."""
    return date.today()
