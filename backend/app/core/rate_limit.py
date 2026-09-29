"""Rate limiting por IP para los endpoints de lectura (T013, FR-012)."""

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


def ip_real(request: Request) -> str:
    """IP del cliente. Detras del Cloudflare Tunnel llega en `CF-Connecting-IP`;
    sin el, todas las peticiones parecerian venir de la IP del tunel."""
    return request.headers.get("cf-connecting-ip") or get_remote_address(request)


def crear_limiter() -> Limiter:
    # Almacenamiento en memoria: basta para una unica instancia de la API
    return Limiter(key_func=ip_real)
