# Modelo de Datos (Fase 1): Backend (API + Base de Datos) para HouseScore

Basado en las Key Entities de [spec.md](spec.md) y en los ficheros actuales
que sustituye (`frontend/datos/listings.json`, `historico_diario.json`,
`config/precios_referencia.json`).

## Listing

Un piso/vivienda scrapeado, en su estado más reciente conocido.

| Campo | Tipo | Notas |
|---|---|---|
| `id` | UUID / serial (clave primaria interna) | Generado por la BBDD |
| `url` | string, único, no nulo | Identificador natural del listing (FR-009); origen de la fuente |
| `titulo` | string | |
| `precio` | entero (céntimos o € — decidir en implementación), nullable | `null` posible si el listing llega sin precio en una pasada |
| `m2` | entero, nullable | Ausente ⇒ `datos_insuficientes = true` |
| `habitaciones` | entero, nullable | |
| `banos` | entero, nullable | |
| `municipio` | string, no nulo | Debe pertenecer al alcance de Principio V (Madrid Sur / Toledo Norte activo) |
| `fuente` | enum(`pisos.com`, `idealista`) | |
| `score` | float, nullable | Calculado por el motor de scoring; `null` si `datos_insuficientes` |
| `datos_insuficientes` | boolean, no nulo, default `false` | FR-005 |
| `estado` | enum(`activo`, `retirado`) | FR-007 |
| `primera_aparicion` | fecha, no nula | Para calcular antigüedad del listing |
| `ultima_aparicion` | fecha, no nula | Usada para el umbral de 7 días de retirado (FR-007) |
| `creado_en` / `actualizado_en` | timestamp | Auditoría estándar |

**Reglas de validación**:
- `url` es la clave de deduplicación (FR-009): una pasada que repite una
  `url` existente actualiza el registro, no crea uno nuevo.
- Si `m2` es `null` ⇒ `datos_insuficientes = true` y `score = null`
  (Principio I / FR-005).
- `municipio` debe pertenecer a la lista de municipios activos; los de
  Toledo Norte bloqueados se descartan antes de llegar a esta tabla
  (FR-006) — no se persisten ni siquiera como `retirado`.

**Transiciones de estado**: `activo → retirado` cuando `ultima_aparicion`
lleva más de 7 días sin actualizarse respecto a la fecha de la última
pasada global (FR-007). No hay transición inversa automática: si reaparece,
se trata como reactivación (`retirado → activo`) al recibir una nueva
pasada con esa `url`.

## HistorialPrecio

Registra cada bajada de precio confirmada de un listing (FR-004).

| Campo | Tipo | Notas |
|---|---|---|
| `id` | serial | |
| `listing_id` | FK → Listing | |
| `precio_anterior` | entero | |
| `precio_nuevo` | entero | |
| `fecha_cambio` | fecha | |

**Regla de negocio migrada de `listings_store.py`**: una bajada de más del
40% en una sola pasada no se acepta como definitiva hasta confirmarse con
un valor similar en la pasada siguiente (`OUTLIER_DROP_RATIO`); hasta
confirmarse, el precio mostrado sigue siendo el anterior y el nuevo queda
como candidato (campo interno equivalente a `_candidate_price`, no
necesariamente expuesto por la API).

## PasadaDiaria (histórico agregado)

Una fila por día con las métricas agregadas de esa pasada — alimenta el
endpoint de histórico (FR-013) y los gráficos de evolución del dashboard.

| Campo | Tipo | Notas |
|---|---|---|
| `fecha` | fecha, única | |
| `total_listings` | entero | |
| `score_medio` | float, nullable | Excluye listings `datos_insuficientes` |
| `precio_medio` | float, nullable | |
| *(resto de agregados que ya calcula `historico_diario.json`)* | — | Se migran tal cual, sin inventar métricas nuevas fuera de alcance (Principio V) |

## PrecioReferencia

Mediana de €/m² por municipio, usada por el motor de scoring cuando un
listing no aporta m² fiables.

| Campo | Tipo | Notas |
|---|---|---|
| `municipio` | string, único | |
| `mediana_eur_m2` | float | |
| `actualizado_en` | timestamp | Se recalcula en cada pasada, igual que hoy en `config/precios_referencia.json` |

## Relaciones

```text
Listing 1 ──── N HistorialPrecio
Listing N ──── 1 PrecioReferencia   (por municipio, no FK estricta —
                                      join lógico por nombre de municipio)
PasadaDiaria                         (tabla independiente, agregados por fecha)
```

## Migración de datos existentes (SC-004)

Los ficheros actuales se cargan una única vez en las tablas de arriba como
parte de la implementación (no de este plan): `listings.json` → `Listing`,
`historico_diario.json` → `PasadaDiaria`, y las bajadas de precio ya
registradas en `listings.json` (`price_drop`/`previous_price`) → filas de
`HistorialPrecio`. Cero pérdida de datos históricos, tal como exige SC-004.
