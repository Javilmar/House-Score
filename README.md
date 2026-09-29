# Dashboard de Búsqueda de Vivienda

Dashboard en Streamlit que visualiza listings de vivienda (Madrid Sur + Toledo
Norte) con scoring a medida. Un scorer (3 lotes con Playwright) corre cada día
en el ordenador local, guarda cada pasada en una API con base de datos
(`backend/`) y el dashboard lee de esa API.

## Estructura

```
HouseScore/
├── frontend/
│   ├── dashboard/app.py        # la app Streamlit (cliente de la API)
│   ├── dashboard/api_datos.py  # traduce la API a las columnas de la app
│   ├── config/                 # precios de referencia por municipio (los usa el scorer)
│   └── requirements.txt
├── backend/                    # API FastAPI + PostgreSQL (Docker), scorer y utilidades
│   ├── app/                    # API: GET /listings, GET /historico, POST /ingest
│   ├── worker/scraper/         # el scorer (3 lotes) y el cliente que publica en la API
│   └── ops/                    # lanzador del cron de hermes, backups, túnel, tareas
└── specs/                      # specs de Spec Kit (001 backend, 002 dashboard)
```

Front y backend son directorios hermanos en el mismo repo (monorepo). El
dashboard **no lee ficheros**: pide los datos a la API (`HOUSESCORE_API_URL`,
por defecto `http://127.0.0.1:8000`). Ver [`backend/README.md`](backend/README.md)
para arrancar todo, y [GUIA-SPEC-KIT.md](GUIA-SPEC-KIT.md) y
[.specify/memory/constitution.md](.specify/memory/constitution.md) para el
flujo de desarrollo.

## Ver en local

```bash
cd backend && docker compose up -d          # API + base de datos
pip install -r frontend/requirements.txt
streamlit run frontend/dashboard/app.py
```

Si la API no responde, el dashboard muestra un aviso con la dirección consultada
y ninguna cifra. Con otra API: `HOUSESCORE_API_URL=http://otra:8000 streamlit run ...`.

## Actualización automática de datos

El job `Buscador Pisos` de hermes (`0 9 * * *`) ejecuta el lanzador
`backend/ops/hermes_launcher.py`, que lanza el scorer del repo
(`backend/worker/scraper/property_scorer_all.py`); cada lote envía su pasada a la
API (`POST /ingest`). No hay `git commit`/`push` de datos: los datos viven en
PostgreSQL, con copia diaria en OneDrive (`ops/backup.ps1`). Detalle en
[`backend/README.md`](backend/README.md).

## Despliegue en la nube (pendiente)

El dashboard en Streamlit Community Cloud necesita que la API sea accesible desde
fuera: falta el túnel `cloudflared` (cuenta y dominio de Cloudflare; ver
`backend/ops/cloudflared.yml`, que publica solo las rutas de lectura). Hasta
entonces se usa en local.

## Harness de desarrollo con IA

Este repo usa **Claude Code** con **[Spec Kit](https://github.com/github/spec-kit)**
como harness de desarrollo dirigido por especificación. Ver
[GUIA-SPEC-KIT.md](GUIA-SPEC-KIT.md) para el flujo completo. Los ficheros
relevantes:

- `.specify/memory/constitution.md` — principios no negociables del proyecto.
- `.specify/templates/`, `.specify/scripts/` — plantillas y scripts internos
  de Spec Kit.
- `.claude/skills/speckit-*/` — comandos `/speckit-*` (constitution, specify,
  plan, tasks, implement, converge, clarify, analyze, checklist,
  taskstoissues).

No hace falta instalar nada aparte: son ficheros de configuración/instrucciones
que Claude Code (u otro IDE compatible con Spec Kit) lee automáticamente al
abrir el repo.

## Decisiones de producto más importantes

(detalle completo en [`frontend/dashboard/FUNCIONALIDADES.md`](frontend/dashboard/FUNCIONALIDADES.md))

- **Precio máximo scrapeado:** ≤ 300.000 €.
- **Fuentes:** pisos.com (fiable) + idealista (best-effort, puede bloquear
  DataDome).
- **Zona de cobertura:** Madrid Sur (18 municipios) + Toledo Norte (5
  municipios de interés activo). **Toledo capital queda excluida** (>55 min,
  mercado distinto).
- **Motor de scoring único** en `backend/worker/scraper/property_scorer_common.py` (0–100 puntos); si un
  listing no tiene m² fiable se marca `datos_insuficientes` y queda
  "sin valorar" en vez de forzar un cálculo erróneo.
- **Flujo de datos:** scorer (3 lotes) → API `POST /ingest` (deduplicación por
  url, detección de bajadas de precio y de pisos retirados) → PostgreSQL →
  API `GET /listings` y `/historico` → `app.py` (Streamlit).
- **Diseño:** modo oscuro siempre, un único color de acento (`#6366f1`), sin
  emojis en la UI (se usan iconos SVG Lucide vía `icon()`).
- **Sin dependencias nuevas** salvo justificación explícita — stack actual:
  `streamlit`, `pandas`, `plotly`, `requests`, stdlib Python.
