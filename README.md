# HouseScore

Buscador de vivienda (Madrid Sur + Toledo Norte) con scoring a medida. Un scorer
(3 lotes con Playwright) corre cada día en el ordenador del propietario y publica
cada pasada en una API con base de datos; el front web, estático, la lee de esa API.

- **Front publicado:** <https://housescore.errinostrich.workers.dev>
- **API publicada:** <https://house-score.onrender.com> (plan gratuito: tras un rato
  sin uso se duerme y la primera petición tarda hasta ~1 min; el front lo avisa con
  «Despertando el servidor…»)

## Estructura

```
HouseScore/
├── frontend/
│   ├── web/                    # front estático (React + Vite + TypeScript), Cloudflare Worker
│   │   ├── src/                # domain/ (lógica pura), views/, components/, state/, styles/
│   │   ├── public/assets/      # geometrías y datos de los mapas
│   │   ├── tests/              # unit/, components/, e2e/ (Playwright), fixtures
│   │   └── FUNCIONALIDADES.md  # referencia funcional del front
│   └── scripts/                # build_mapa_assets.py: regenera public/assets/
├── backend/                    # API FastAPI + PostgreSQL, scorer y utilidades
│   ├── app/                    # API: GET /listings, GET /historico, POST /ingest
│   ├── worker/scraper/         # el scorer (2 lotes) y el cliente que publica en la API
│   └── ops/                    # lanzador del cron de hermes, backups y tareas programadas
├── neon.ts                     # configuración del proyecto Neon (raíz)
└── specs/                      # histórico de diseño (001 backend, 002 y 003 front); no se mantiene
```

Front y backend son directorios hermanos en el mismo repo (monorepo). El front
**no lee ficheros de datos**: pide `GET /listings` y `GET /historico` a la API
(`VITE_API_URL`, por defecto `http://127.0.0.1:8000`). Ver
[`backend/README.md`](backend/README.md) y [`frontend/web/FUNCIONALIDADES.md`](frontend/web/FUNCIONALIDADES.md).

## Flujo de datos

```
scorer (PC del propietario, hermes 09:00)
   └─ POST /ingest ─▶ API en Render ─▶ Neon (PostgreSQL)
                          └─ GET /listings, GET /historico ─▶ front en Cloudflare (navegador)
```

El job `Buscador Pisos` de hermes (`0 9 * * *`) ejecuta el lanzador
`backend/ops/hermes_launcher.py`, que lanza el scorer del repo
(`backend/worker/scraper/property_scorer_all.py`); cada lote envía su pasada a la
API de Render (`POST /ingest`, con `INGEST_SECRET`). No hay `git commit`/`push`
de datos: viven en Neon, con copia en OneDrive (`backend/ops/backup.ps1`).
Detalle en [`backend/README.md`](backend/README.md).

## Ver en local

```bash
# API local con su base de datos
cd backend && docker compose up -d

# Front
cd frontend/web
npm ci
npm run dev
```

Por defecto el front consulta `http://127.0.0.1:8000`. Para apuntar a otra API
(por ejemplo la de Render): `VITE_API_URL=https://house-score.onrender.com npm run dev`.
Si la API no responde, el front muestra el error y la dirección consultada, sin cifras.

Tests del front (en `frontend/web`):

```bash
npm run typecheck
npm test                                     # unitarios y de componentes (Vitest)
npm run test:e2e                             # Playwright con API simulada
BASE_URL=https://housescore.errinostrich.workers.dev npm run test:smoke   # contra el despliegue
```

Tests del backend: ver [`backend/README.md`](backend/README.md).

## Despliegue

### API en Render

Servicio web con **Root Directory** `backend` y entorno **Docker**. Variables:

| Variable | Uso |
|---|---|
| `DATABASE_URL` | Conexión a Neon (con pooler) |
| `DATABASE_URL_UNPOOLED` | Conexión directa a Neon (migraciones y `pg_dump`) |
| `INGEST_SECRET` | Secreto Bearer que exige `POST /ingest` |
| `CORS_ORIGINS` | Orígenes del front que pueden leer la API (p. ej. `https://housescore.errinostrich.workers.dev`) |
| `PORT` | Puerto que asigna Render |

### Front en Cloudflare

Worker de ficheros estáticos (`frontend/web/wrangler.jsonc`) conectado al repo con
Workers Builds: **Root directory** `frontend/web`, **build** `npm run build`,
**deploy** `npx wrangler deploy`. Variables de *build* (se incrustan al compilar):
`VITE_API_URL=https://house-score.onrender.com` y `NODE_VERSION=22`.

### Base de datos en Neon

Proyecto de Neon con la base de HouseScore, configurado en `neon.ts` (raíz del repo,
política de ramas). Las cadenas de conexión viven en `.env.local` (raíz, no versionado) y
las usa `backend/ops/backup.ps1`. Detalle de copias y
restauración en [`backend/README.md`](backend/README.md).

## Reglas de trabajo

- **Un solo motor de scoring** (`property_scorer_common.py`): el front muestra el score y su
  desglose tal como llegan de la API; nunca lo recalcula. Sin m² fiable → "sin valorar".
- **Tests para la lógica**: todo cambio de comportamiento en el scoring, la API o el dominio
  del front (`frontend/web/src/domain/`) lleva su test. Retoques visuales no necesitan test.
- **Alcance fijo**: Madrid Sur + Toledo Norte, ≤ 300.000 €. Ampliar zonas, techo o portales
  es una decisión explícita, no un efecto colateral.
- **Secretos fuera del repo**: `.env.local` y `backend/.env` están
  en `.gitignore`; en producción las variables viven en Render.
- **Migraciones sin restos**: cuando se sustituye una pieza, la anterior se borra (queda una
  etiqueta git como referencia), sin modos de compatibilidad.
- **Coste 0 €**: Neon, Render y Cloudflare en plan gratuito.

Las carpetas `specs/` documentan cómo se diseñaron el backend y el front; son histórico y
no hace falta actualizarlas.

## Historia

El front original era un dashboard Streamlit. Se retiró en bloque (corte limpio,
sin ruta de compatibilidad). La etiqueta git `pre-retirada-streamlit`
es el último commit que lo contiene; `pre-retirada-fase1` es el último con los JSON
diarios de datos.

## Decisiones de producto más importantes

(detalle completo en [`frontend/web/FUNCIONALIDADES.md`](frontend/web/FUNCIONALIDADES.md))

- **Precio máximo scrapeado:** ≤ 300.000 €.
- **Fuentes:** pisos.com (Madrid Sur + Toledo Norte) y fotocasa.es (en el lote de Madrid Sur,
  `backend/worker/scraper/property_scorer_madrid.py`; se omite esa pasada si
  bloquea).
- **Zona de cobertura:** Madrid Sur (18 municipios) + Toledo Norte (5
  municipios de interés activo). **Toledo capital queda excluida** (>55 min,
  mercado distinto).
- **Motor de scoring único** en `backend/worker/scraper/property_scorer_common.py` (0–100 puntos); si un
  listing no tiene m² fiable se marca `datos_insuficientes` y queda
  "sin valorar" en vez de forzar un cálculo erróneo.
- **Flujo de datos:** scorer (2 lotes, PC del propietario) → `POST /ingest` en la API de
  Render (deduplicación por url, detección de bajadas de precio y de pisos
  retirados) → Neon → `GET /listings` y `/historico` → front estático en Cloudflare.
- **Diseño:** modo oscuro siempre, un único color de acento (`#6366f1`), sin
  emojis en la UI (iconos SVG propios en `Icon`).
- **Sin dependencias nuevas** salvo justificación explícita — stack del front:
  React, Vite, TypeScript y `plotly.js-dist-min`; tests con Vitest y Playwright.
