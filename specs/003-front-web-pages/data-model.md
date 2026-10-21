# Modelo de datos del front

El front no persiste nada: trabaja en memoria con lo que sirve la API. La
base de datos y su esquema no cambian (spec 001, `data-model.md`).

## ListingApi (respuesta de `GET /listings`, `backend/app/schemas.py:ListingOut`)

| Campo | Tipo | Notas |
|---|---|---|
| `url` | string | identidad del listing |
| `titulo` | string | |
| `precio` | int \| null | euros |
| `m2`, `habitaciones`, `banos` | int \| null | |
| `municipio` | string | |
| `fuente` | string | `pisos.com` \| `idealista` |
| `score` | number \| null | 0–100, calculado por el scorer (Principio I) |
| `datos_insuficientes` | bool | true → "sin valorar" |
| `estado` | string | activo \| retirado |
| `primera_aparicion`, `ultima_aparicion` | fecha ISO | |
| `precio_anterior`, `bajada_precio` | int \| null | bajada detectada en ingest |
| `detalle` | objeto | `score_details`, `description`, `eur_m2`, `features`, `location`, `floor`, `year_built`, `energy_rating`, … |

## Listing (modelo del front, `src/api/mapeo.ts`)

Mismos nombres de columna que hoy usa `app.py` (`title`, `price`, `rooms`, …)
para poder trasladar cada regla del inventario sin renombrados. La tabla de
traducción campo a campo es la de `api_datos.py` (ver
`inventario-dashboard.md` §datos) y se cubre con un test de mapeo.

Campos derivados (lógica pura en `src/domain/`, fórmulas en el inventario):
zona (Madrid Sur / Toledo Norte / —), tipo de vivienda (Obra nueva /
Segunda mano), €/m², días en mercado, nuevo (criterio de Novedades),
porcentaje de bajada, retirado, desglose de score por bloques.

## PasadaDiaria (respuesta de `GET /historico`, `PasadaDiariaOut`)

`fecha`, `total_listings`, `score_medio`, `precio_medio`, `precio_min`, `precio_max`.

## Estado de carga (máquina de estados de `src/state/carga.ts`)

```text
cargando ──(3 s sin respuesta)──▶ despertando ──(respuesta)──▶ listo | sin_datos
   │                                   │
   └──────────(error o 90 s)───────────┴──▶ error{tipo, url} ──(Reintentar)──▶ cargando
```

`tipo` ∈ {`no_disponible`, `limite`, `http`, `ilegible`}. Sin transiciones
automáticas desde `error` (FR-005).

## Estado de vista (hash de la URL, `contracts/vistas.md`)

Vista activa y sus parámetros (filtros de Listados, top N, precarga de
Hipoteca, capa de Mapas). Recargar la página restaura la vista.

## Recursos estáticos del mapa

`public/assets/municipios_zona.geojson` (clave `cod_ine`),
`criminalidad.csv`, `secciones_renta.geojson` (clave `cusec`). Contenido sin
cambios; se descargan solo al abrir Mapas.
