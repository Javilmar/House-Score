# Investigación (Fase 0): Front web en la nube

**Spec**: [spec.md](spec.md) | **Fecha**: 2026-10-21

## 1. Stack del front

**Decisión**: Vite + React 19 + TypeScript, compilado a ficheros estáticos.

**Motivo**: 8 vistas con estado compartido (filtros, listing seleccionado,
calculadora precargada) y componentes repetidos (cards, badges, desglose de
score) piden un modelo de componentes; React es el ejemplo que da la propia
constitución para la Fase 3. Vite produce un `dist/` estático que Cloudflare
Pages sirve sin funciones de servidor.

**Alternativas consideradas**:
- *Next.js (export estático)*: añade enrutado y SSR que no se usan; más
  configuración para el mismo resultado estático.
- *TypeScript sin framework*: menos dependencias, pero reimplementar estado y
  re-render de 8 vistas a mano es más código y más superficie de bugs.
- *stlite*: descartado en la spec (Principio II).

## 2. Gráficos y mapas

**Decisión**: Plotly.js (`plotly.js-dist-min`), cargado bajo demanda solo en
"Evolución y análisis" y "Mapas".

**Motivo**: el dashboard actual ya usa Plotly (barras, líneas, histograma,
eje dual, `choropleth_map` sobre MapLibre). Usar la misma librería permite
reproducir cada gráfico con la misma configuración (tipos, bins, escalas de
color, `zoom`, `center`, estilo de mapa) y verificar la paridad por
comparación directa. Cargarla bajo demanda evita penalizar la primera
pantalla (SC-002).

**Alternativas consideradas**:
- *ECharts + MapLibre*: dos librerías y rediseñar cada gráfico; la paridad
  pasa a ser visual y subjetiva.
- *Chart.js / uPlot*: sin mapas coropléticos; obligaría a una segunda librería.

## 3. Tabla de listados y rendimiento

**Decisión**: componente propio; filtrado y ordenación en memoria sobre el
array completo; filas renderizadas con `content-visibility: auto` para no
pintar las que están fuera de pantalla.

**Motivo**: ~2.000 listings caben en memoria; filtrar y ordenar arrays de
ese tamaño cuesta pocos milisegundos (SC-006 < 200 ms). Una librería de
tablas no aporta nada que no sea ordenar por columna.

**Alternativas consideradas**: *TanStack Table / virtualización*: dependencia
extra justificable solo si la medición en T-rendimiento supera el objetivo.

## 4. Navegación entre vistas y precarga de la hipoteca

**Decisión**: estado de la vista en el hash de la URL (`#/hipoteca?precio=…&tipo=…&ccaa=…`,
`#/top?id=…`).

**Motivo**: sustituye el apaño actual (`sessionStorage._sw_tab` +
`MutationObserver` + query params) por enlaces directos que funcionan al
recargar y se pueden compartir. Con hash no hace falta configurar reglas de
reescritura en Pages.

## 5. Carga de datos, arranque en frío y errores

**Decisión**: `fetch` con `AbortController`. Primera petición con espera
máxima de 90 s (FR-004); a los 3 s sin respuesta se muestra "Despertando el
servidor…". Errores clasificados en: red/tiempo agotado, HTTP 429, HTTP ≥
400, JSON ilegible, y respuesta vacía (estado "sin datos" distinto). Un
botón "Reintentar" relanza la carga; sin reintentos automáticos (FR-005).

**Motivo**: Render gratis retiene la primera petición mientras arranca el
servicio (≈ 1 min); un tiempo máximo corto (los 15 s actuales del dashboard)
convertiría cada arranque en frío en un error.

## 6. CORS y exposición de la API

**Decisión**: `CORSMiddleware` de FastAPI (incluido en Starlette, sin
dependencia nueva), orígenes desde la variable `CORS_ORIGINS` (lista separada
por comas: el origen `*.pages.dev` del front y `http://localhost:5173`),
solo método `GET`, sin credenciales. `POST /ingest` no necesita CORS: lo
llama el scorer, no un navegador; sigue protegido por `INGEST_SECRET`.

## 7. IP real para el rate limiting en Render

**Decisión**: arrancar uvicorn con `--proxy-headers --forwarded-allow-ips='*'`
en la imagen y conservar `cf-connecting-ip` como primera fuente.

**Motivo**: detrás del proxy de Render la conexión llega desde el proxy;
sin cabeceras de reenvío todas las visitas compartirían cupo. Confiar en
cualquier origen es aceptable porque el contenedor solo es alcanzable a
través del proxy de Render [INFERENCIA: verificar en el despliegue con una
petición que muestre la IP vista por la API, tarea de verificación].

## 8. Scorer contra una API que se duerme

**Decisión**: `verificar_api` reintenta con espera creciente hasta ~3 min
antes de abortar el lote; el resto de llamadas mantiene sus tiempos (60 s
lectura, 120 s ingest con 3 reintentos).

**Motivo**: el job de las 09:00 casi siempre encontrará la API dormida; hoy
`verificar_api` hace un único intento y el lote se abortaría.

## 9. Migración del histórico

**Decisión**: `pg_restore --no-owner --no-privileges --clean --if-exists`
del volcado `housescore-2026-10-21_1354.dump` contra la conexión **directa**
de Neon, ejecutado con la imagen `postgres:18-alpine` (pg_restore 18 lee
volcados de 16). Verificación: restaurar el mismo volcado en un contenedor
efímero local y comparar recuentos por tabla con Neon.

**Motivo**: la skill de Neon exige conexión directa para `pg_dump`/`pg_restore`;
el volcado ya incluye `alembic_version = 0001`, coherente con el esquema.

## 10. Despliegue del front

**Decisión**: integración Git de Cloudflare Pages: raíz `frontend/web`,
comando `npm run build`, salida `dist`, variable `VITE_API_URL` con la URL de
Render, `NODE_VERSION=22`.

**Motivo**: igual que Render, despliega solo al hacer push; no hay secretos
en el front (la API de lectura es pública).

## 11. Copias de seguridad

**Decisión**: adaptar `backend/ops/backup.ps1` para volcar Neon (conexión
directa, `pg_dump -Fc` desde `postgres:18-alpine`) a OneDrive con la misma
rotación.

**Motivo**: la restauración instantánea del plan gratuito de Neon cubre una
ventana corta; la spec 001 exigía copias fuera de la plataforma (SC-007 de
la 001), y el corte no debe perder esa garantía.

## 12. Retirada de Streamlit y de la infraestructura local

**Decisión** (corte duro, Principio VI): se eliminan `frontend/dashboard/app.py`,
`api_datos.py`, `frontend/requirements.txt` y la documentación que los
describe; los assets del mapa pasan a `frontend/web/public/assets/` y
`build_mapa_assets.py` a `frontend/scripts/` escribiendo allí. Se elimina
`backend/ops/cloudflared.yml` (T050 de la 001 deja de aplicar). Se conserva
`docker-compose.yml` solo para desarrollo y tests locales.
`frontend/config/precios_referencia.json` no se toca (lo usa el scorer).
