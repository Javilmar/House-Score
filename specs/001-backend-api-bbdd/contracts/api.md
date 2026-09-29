# Contrato de la API (Fase 1): Backend HouseScore

Todos los endpoints devuelven JSON. Los de lectura son públicos y llevan
rate limiting por IP (FR-012); el de ingesta requiere el secreto compartido
descrito en `research.md` §4 (FR-010/FR-011).

## GET /listings

Lista los listings vigentes con su score ya calculado.

**Query params** (todos opcionales):
- `municipio` — filtra por municipio.
- `incluir_retirados` — booleano, default `false`.

**200 OK**:
```json
[
  {
    "url": "https://...",
    "titulo": "Piso en Chamberí",
    "precio": 250000,
    "m2": 80,
    "habitaciones": 3,
    "banos": 2,
    "municipio": "Alcorcón",
    "fuente": "pisos.com",
    "score": 78.5,
    "datos_insuficientes": false,
    "estado": "activo",
    "primera_aparicion": "2026-07-14",
    "ultima_aparicion": "2026-09-08",
    "precio_anterior": 260000,
    "bajada_precio": 10000,
    "detalle": { "score_details": ["..."], "eur_m2": 3125, "description": "..." }
  }
]
```

`fuente` es texto libre (`pisos.com`, `idealista`, y `fotocasa.es` en los datos historicos).
`precio_anterior` y `bajada_precio` son la marca de bajada de la ultima pasada (null si no hay).
`detalle` lleva el resto de campos que hoy usa el dashboard (`score_details`, `eur_m2`,
`description`, ...), para que el front pueda migrar sin perder informacion.

**429 Too Many Requests**: si se supera el límite de rate limiting (FR-012).

## GET /historico

Sirve el histórico agregado por día (FR-013), para los gráficos de
evolución.

**Query params** (opcionales): `desde`, `hasta` (fechas ISO).

**200 OK**:
```json
[
  {
    "fecha": "2026-09-08",
    "total_listings": 506,
    "score_medio": 14.2,
    "precio_medio": 245000,
    "precio_min": 16900,
    "precio_max": 511500
  }
]
```

**429 Too Many Requests**: igual que `/listings`.

## POST /ingest

Endpoint de escritura: el scraper local envía aquí cada pasada completa,
por `http://localhost:8000/ingest`. **No es de uso público** (FR-010/FR-011):
el Cloudflare Tunnel no enruta esta ruta (responde 404 desde fuera), y
además requiere cabecera `Authorization: Bearer <secreto>`.

**Request body**:
```json
{
  "listings": [
    {
      "url": "https://...",
      "titulo": "Piso en Chamberí",
      "precio": 250000,
      "m2": 80,
      "habitaciones": 3,
      "banos": 2,
      "municipio": "Alcorcón",
      "fuente": "pisos.com",
      "score": 78.5,
      "datos_insuficientes": false,
      "detalle": {}
    }
  ]
}
```

`datos_insuficientes` y `detalle` son opcionales. El cliente del scraper traduce el formato del
scorer (`title`, `price`, `rooms`, ...) a este contrato (`app/services/formato_scraper.py`).

**Comportamiento**:
- Deduplica por `url` (FR-009): actualiza el listing existente o crea uno
  nuevo.
- Aplica la regla de bajada de precio confirmada/candidata (ver
  `data-model.md` § HistorialPrecio).
- Descarta antes de persistir cualquier listing de un municipio bloqueado
  de Toledo Norte (FR-006).
- Marca `datos_insuficientes` cuando falte `m2` (FR-005).
- Actualiza `PasadaDiaria` del día con los agregados resultantes.
- Marca como `retirado` cualquier listing activo que no aparezca en esta
  pasada y lleve más de 7 días sin aparecer (FR-007).

**201 Created**: resumen de la pasada procesada.
```json
{
  "listings_procesados": 506,
  "nuevos": 3,
  "actualizados": 480,
  "descartados_bloqueados": 2,
  "retirados": 1
}
```

**401 Unauthorized**: si falta o no coincide el secreto compartido.

**500 Internal Server Error**: si falla la persistencia — el fallo se
registra en el log (FR-014), sin notificación activa en esta fase.
