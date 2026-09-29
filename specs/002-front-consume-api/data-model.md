# Modelo de Datos (Fase 1): El dashboard consume la API

Esta funcionalidad no crea entidades nuevas: traduce las que sirve la API de la
spec 001 al formato de columnas que ya usa `app.py`, en un único punto
(`api_datos.py`).

## Listing: `GET /listings` → DataFrame de `cargar_datos()`

| API (contrato spec 001) | Columna del dashboard | Notas |
|---|---|---|
| `titulo` | `title` | |
| `precio` | `price` | numérico; `null` → `NaN` |
| `m2` | `m2` | `null` → `NaN` (antes `0`) |
| `habitaciones` | `rooms` | |
| `banos` | `bathrooms` | |
| `url` | `url` | |
| `fuente` | `source` | `pisos.com`, `idealista`, `fotocasa.es` |
| `municipio` | `municipio` | id con guiones bajos, como hoy |
| `score` | `score` | `null` si `datos_insuficientes` → `NaN` |
| `datos_insuficientes` | `datos_insuficientes` | |
| `estado` (`activo`/`retirado`) | `status` (`active`/`delisted`) | la app filtra por `"active"` y `"delisted"` |
| `primera_aparicion` | `first_seen` | fecha → `Timestamp` |
| `ultima_aparicion` | `last_seen` | fecha → `Timestamp` |
| `bajada_precio` | `price_drop` | `null` → `NaN` |
| `precio_anterior` | `previous_price` | `null` → `NaN` |
| `detalle.*` | columnas con el mismo nombre | ver abajo |

### Campos de `detalle` (se vuelcan como columnas, tal cual)

`location`, `description`, `floor`, `year_built`, `conservation`,
`energy_rating`, `features`, `detail_features`, `pisos_id`, `score_details`,
`exterior`, `cumple_requisitos`, `crashed_municipio` y cualquier otro campo que
traiga el scorer. `eur_m2` de `detalle` se ignora: `cargar_datos()` lo recalcula
como `price / m2`, igual que hoy.

**Reglas**:
- Si falta una clave de `detalle` o `detalle` está vacío, la columna queda
  ausente o `NaN` en esas filas; el resto de la app ya tolera datos
  incompletos.
- Una clave de `detalle` nunca pisa una columna principal (si coincidiera, gana
  la principal).
- El orden final es el de hoy: `score` descendente, `NaN` al final.

## Pasada diaria: `GET /historico` → DataFrame de `cargar_historico()`

| API | Columna del dashboard |
|---|---|
| `fecha` | `fecha` (`Timestamp`) |
| `total_listings` | `count` |
| `score_medio` | `avg_score` |
| `precio_medio` | `avg_price` |
| `precio_min` | `min_price` |
| `precio_max` | `max_price` |

Orden ascendente por `fecha`. Lista vacía → DataFrame vacío (el gráfico ya se
oculta cuando hay menos de dos filas).

## Errores

`ApiNoDisponible(mensaje, url)`: conexión, tiempo agotado, HTTP ≠ 200 (mensaje
propio para 429) o cuerpo que no es una lista JSON. No es una entidad de datos,
pero es parte del contrato del adaptador (ver `contracts/api-datos.md`).
