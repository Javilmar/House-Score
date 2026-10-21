# Plan de Implementación: Front web en la nube (Fase 3)

**Rama**: `003-front-web-pages` | **Fecha**: 2026-10-21 | **Spec**: [spec.md](spec.md)

**Entrada**: Especificación de la funcionalidad en `/specs/003-front-web-pages/spec.md`

## Resumen

Sustituir el dashboard de Streamlit por un front web estático (Vite + React +
TypeScript) publicado en Cloudflare Pages, con paridad funcional en las 8
vistas, que lee de la API FastAPI desplegada en Render sobre PostgreSQL en
Neon. El scorer sigue en el PC del propietario y publica en la API en la
nube. Se migra el histórico desde el volcado facilitado y se retira
Streamlit sin compatibilidad (Principio VI). Detalle de decisiones en
[research.md](research.md); inventario de comportamiento a reproducir en
[inventario-dashboard.md](inventario-dashboard.md).

## Contexto Técnico

**Lenguaje/Versión**: TypeScript 5 (front, Node 22 para compilar); Python 3.11 (API y scorer, sin cambios de versión)

**Dependencias principales**: front: `react`, `react-dom`, `plotly.js-dist-min` (bajo demanda); desarrollo: `vite`, `@vitejs/plugin-react`, `typescript`, `vitest`, `@testing-library/react`, `jsdom`, `@playwright/test`. API: sin dependencias nuevas (`CORSMiddleware` viene con FastAPI)

**Almacenamiento**: PostgreSQL 18 en Neon (rama `production`); la API usa la conexión con pooler y Alembic la directa (ya en `b6c7fd7`)

**Testing**: Vitest + Testing Library (lógica y componentes), Playwright (recorridos de las 8 vistas contra la API simulada y una pasada de humo contra la API real), pytest (API y scorer)

**Plataforma objetivo**: navegadores de escritorio y móvil actuales; Cloudflare Pages (estático); Render (contenedor Docker, plan gratuito)

**Tipo de proyecto**: aplicación web (front estático + API existente)

**Objetivos de rendimiento**: primera pantalla con API despierta < 3 s (SC-002); filtrar/ordenar ~2.000 listings < 200 ms (SC-006)

**Restricciones**: coste 0 € (SC-008); arranque en frío de la API ≈ 1 min aceptado (Clarifications); sin secretos en el front ni en el repo (FR-013); identidad visual actual (FR-011)

**Escala/Alcance**: 1 usuario; ~2.000 listings; 8 vistas; 3 assets de mapa (~3,3 MB en total, carga diferida)

## Constitution Check

*GATE: Debe superarse antes de la Fase 0 de investigación. Volver a comprobar tras el diseño de la Fase 1.*

| Principio | Estado | Cómo se cumple |
|---|---|---|
| I. Motor de scoring único | Cumple | El front muestra `score` y su desglose tal como los sirve la API; no recalcula puntuaciones. "Sin valorar" se respeta (FR-003). |
| II. Fases arquitectónicas | Cumple | Este spec es la transición a la Fase 3 en su propio ciclo. stlite descartado por profundizar en la Fase 2. |
| III. Gateado por el harness | Cumple | Ciclo completo `specify → clarify → plan → tasks → analyze → implement → converge`. |
| IV. TDD | Cumple | Cada tarea de comportamiento empieza por su test (Vitest/Playwright/pytest) en rojo; ver tasks.md. |
| V. Alcance del producto | Cumple | Mismos municipios, techo y fuentes; no se añaden vistas ni datos. |
| VI. Migración dura | Cumple | Se borran `app.py`, `api_datos.py`, `requirements.txt`, `.streamlit/`, sus tests y `cloudflared.yml` en el mismo cambio que publica el front. |
| Restricciones de despliegue | Requiere enmienda | La constitución fija Streamlit Community Cloud como objetivo actual y no decide stack de backend/BD. Se enmienda vía `/speckit-constitution` al cerrar (tarea final). |
| Secretos | Cumple | `DATABASE_URL*`, `INGEST_SECRET` solo en Render y en `backend/.env` local (ignorado); el front no tiene secretos. |

Resultado: sin violaciones que justificar; una enmienda de constitución planificada.

## Estructura del Proyecto

### Documentación (esta funcionalidad)

```text
specs/003-front-web-pages/
├── plan.md
├── research.md
├── inventario-dashboard.md   # comportamiento exacto del dashboard actual (fuente de la paridad)
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── api-lectura.md        # lo que el front consume de la API (y CORS)
│   └── vistas.md             # rutas hash y parámetros de cada vista
└── tasks.md
```

### Código fuente (raíz del repositorio)

```text
backend/
├── app/main.py                 # + CORSMiddleware (CORS_ORIGINS)
├── app/core/config.py          # + cors_origins
├── Dockerfile                  # uvicorn --proxy-headers --forwarded-allow-ips='*'
├── ops/backup.ps1              # vuelca Neon en vez del PostgreSQL local
├── ops/hermes_launcher.py      # tolera arranque en frío; mensaje sin docker compose
├── ops/cloudflared.yml         # ELIMINADO
├── worker/scraper/publicar.py  # verificar_api con reintentos (~3 min)
└── tests/                      # + test_cors.py, + tests de reintento

frontend/
├── config/precios_referencia.json   # sin cambios (lo usa el scorer)
├── scripts/build_mapa_assets.py      # movido; escribe en web/public/assets
├── dashboard/                        # ELIMINADO entero
├── requirements.txt                  # ELIMINADO
└── web/
    ├── index.html
    ├── package.json
    ├── vite.config.ts
    ├── public/assets/                # municipios_zona.geojson, criminalidad.csv, secciones_renta.geojson
    ├── src/
    │   ├── api/                      # cliente HTTP, mapeo API→modelo, clasificación de errores
    │   ├── domain/                   # derivaciones puras: zona, tipo, KPIs, filtros, desglose, hipoteca
    │   ├── state/                    # carga de datos, router por hash
    │   ├── components/               # KpiBar, ScoreBadge, Breakdown, ListingCard, Icon, ...
    │   ├── views/                    # Listados, Top, Novedades, Evolucion, Bajadas, Hipoteca, ComoFunciona, Mapas
    │   └── styles/                   # paleta, tipografías, componentes
    └── tests/
        ├── unit/                     # Vitest: domain/ y api/
        ├── components/               # Vitest + Testing Library
        └── e2e/                      # Playwright: 8 vistas con API simulada + humo contra API real
```

**Decisión de estructura**: se mantiene el monorepo (`backend/` y `frontend/`
hermanos). El front nuevo vive en `frontend/web/` para que Cloudflare Pages
lo construya con raíz propia; `domain/` concentra toda la lógica pura
(testeable sin DOM) y las vistas solo componen.

## Complexity Tracking

Sin violaciones.
