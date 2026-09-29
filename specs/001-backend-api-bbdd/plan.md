# Plan de Implementación: Backend (API + Base de Datos) para HouseScore

**Rama**: `001-backend-api-bbdd` | **Fecha**: 2026-09-08 | **Spec**: [spec.md](spec.md)

**Entrada**: Especificación de la funcionalidad en `specs/001-backend-api-bbdd/spec.md`

## Resumen

Sustituir el flujo actual de HouseScore (scraper local → `guardar.py` →
JSON commiteado en `frontend/datos/` → Streamlit lee el repo) por un backend
con API + base de datos: una API FastAPI que sirve los listings ya
puntuados y el histórico agregado, y el scraper (migrado al repo desde
fuera de él) que escribe cada pasada llamando a un endpoint de ingesta de
esa misma API por `localhost`. Todo corre en el PC del propietario: API +
PostgreSQL en Docker Compose con arranque automático, el scraper como tarea
programada de Windows (usa Playwright/Chromium y una sesión de idealista
capturada a mano, inviable en un datacenter), y un Cloudflare Tunnel que
publica solo las rutas de lectura para el front desplegado en la nube. El
front (Streamlit) no se toca en este plan.

## Contexto Técnico

**Lenguaje/Versión**: Python 3.11 (coincide con el `devcontainer` actual y
con el resto del código Python del proyecto)

**Dependencias principales**: FastAPI, Uvicorn, SQLAlchemy 2.x, Alembic,
Pydantic, slowapi (rate limiting), psycopg (driver PostgreSQL), pytest,
httpx (cliente de test para FastAPI)

**Almacenamiento**: PostgreSQL 16 (contenedor oficial en `docker-compose`,
con volumen persistente en el PC del propietario; copias de seguridad
periódicas con `pg_dump` a otra ubicación, FR-016)

**Testing**: pytest + `httpx.AsyncClient`/`TestClient` de FastAPI, siguiendo
TDD (Principio IV de la constitución): tests de contrato para cada
endpoint, tests de integración para el flujo scraper→API→BBDD, tests
unitarios para las reglas de negocio migradas de `listings_store.py`

**Plataforma objetivo**: PC Windows del propietario. Docker Desktop
(arranque automático con Windows) ejecuta `api` + `db` con
`restart: unless-stopped`; `cloudflared` como servicio de Windows publica
las rutas de lectura; el scraper corre en el host (fuera de Docker) vía
Task Scheduler

**Tipo de proyecto**: web-service (API) + scraper local (proceso programado
en el host) — comparten la misma base de datos a través de la API

**Objetivos de rendimiento**: sin exigencias de alto rendimiento — un único
usuario real, unos pocos cientos de listings vigentes (≈500, según el
volumen actual de `frontend/datos/listings.json`). El objetivo es
disponibilidad y consistencia, no throughput.

**Restricciones**:
- El endpoint de ingesta (escritura) no debe ser invocable desde internet
  (FR-011): el túnel solo enruta `GET /listings` y `GET /historico`, y
  `POST /ingest` exige además el secreto compartido.
- La API y la base de datos deben volver solas tras reiniciar el PC
  (FR-015, SC-006).
- Los endpoints de lectura deben aplicar rate limiting básico por IP
  (FR-012).
- El entorno local completo debe arrancar con un único comando en menos de
  5 minutos (SC-003).
- TDD obligatorio en todo el código no trivial (Principio IV).

**Escala/Alcance**: ≈500 listings vigentes, histórico diario desde julio
de 2026, un único cliente (el dashboard actual) en esta fase.

## Constitution Check

*GATE: Debe superarse antes de la Fase 0 de investigación. Volver a comprobar tras el diseño de la Fase 1.*

| Principio | Evaluación |
|---|---|
| I. Motor de scoring como única fuente de verdad | **PASS, con nota.** El motor de scoring (`property_scorer.py`) no se reimplementa: se migra tal cual junto al scraper. **Hallazgo importante**: hoy el scorer vive fuera de este repositorio, en `~/AppData/Local/hermes/scripts/`, y no está en git; además no es un solo fichero sino cuatro (`property_scorer.py`, `property_scorer_common.py`, `property_scorer_idealista.py`, `property_scorer_all.py`), los dos últimos modificados por última vez el 2026-09-27. Traerlos al repo (bajo `backend/worker/scraper/`) es un prerrequisito de esta implementación — se refleja como tarea explícita en `/speckit-tasks`, no como una violación del principio. `capture_idealista_session.py` y la sesión de cookies (`idealista_session.json`) son locales y con datos de sesión: no se versionan. |
| II. Desacoplo front-datos (fases) | **PASS.** Este plan implementa la Fase 2 (API+BBDD); el front (Fase 2→3) no se toca aquí, tal como fija el spec. |
| III. Desarrollo gateado por el harness | **PASS.** Este plan es en sí mismo un artefacto de la cadena `/speckit-*`. |
| IV. Desarrollo guiado por tests | **PASS, exigido explícitamente.** `/speckit-tasks` debe generar cada tarea de comportamiento con sus tests primero (contrato, integración, unitarios) — ver Contexto Técnico > Testing. |
| V. Disciplina de alcance | **PASS.** No se añaden fuentes, municipios ni cambios de precio máximo; el alcance de datos es el mismo que hoy. |
| VI. Corte duro sin shims | **PASS, con nota.** El flujo de `guardar.py` (JSON + `git push`) se retira por completo al entrar en producción este backend — no se mantiene un doble escritura JSON+BBDD "por si acaso". Esto es aceptable porque, según lo hablado con el propietario, Streamlit deja de mantenerse activamente de todos modos; no hace falta seguir alimentándolo con JSON mientras se prepara su propio spec de migración a consumir la API. |

Ninguna violación requiere justificación en Complexity Tracking.

## Estructura del Proyecto

### Documentación (esta funcionalidad)

```text
specs/001-backend-api-bbdd/
├── plan.md              # Este fichero
├── research.md          # Fase 0
├── data-model.md         # Fase 1
├── quickstart.md         # Fase 1
├── contracts/            # Fase 1
│   └── api.md
└── tasks.md              # Fase 2 (/speckit-tasks, no este comando)
```

### Código fuente (raíz del repositorio)

```text
backend/
├── app/
│   ├── main.py                 # arranque de la app FastAPI
│   ├── api/
│   │   ├── routes_listings.py  # GET /listings, GET /historico (públicos, rate-limited)
│   │   └── routes_ingest.py    # POST /ingest (protegido por secreto compartido)
│   ├── models/                 # modelos SQLAlchemy: Listing, PriceHistory, DailySnapshot, ReferencePrice
│   ├── db/                     # engine, sesión, Alembic
│   └── core/                   # config, rate limiting, logging
├── worker/
│   └── scraper/                 # scorer migrado (4 ficheros) + cliente que llama a POST /ingest + run_scraper.ps1 (Task Scheduler)
├── tests/
│   ├── contract/                # un test por endpoint público/de ingesta
│   ├── integration/              # flujo scraper → API → BBDD de extremo a extremo
│   └── unit/                     # reglas migradas de listings_store.py (price_drop, dedupe, delisted...)
├── alembic/                      # migraciones versionadas
├── Dockerfile
├── docker-compose.yml            # api + postgres (restart: unless-stopped); el scraper corre en el host
├── ops/                          # cloudflared (config del túnel), backup de Postgres, tarea programada
└── requirements.txt / pyproject.toml

frontend/        # sin cambios en este plan
```

**Decisión de estructura**: se usa `backend/` (ya reservado en la raíz del
monorepo, ver README.md) como único proyecto, con dos puntos de entrada
(`app/main.py` para la API, `worker/scraper/` para el scraper). El scraper
solo habla con la API por HTTP, no importa `app/models/`. No se crean
paquetes ni repos separados para API y scraper — es innecesario a esta
escala.

## Complexity Tracking

*Sin violaciones que justificar.*

## Re-chequeo de Constitution Check (post-Fase 1)

Tras diseñar `data-model.md`, `contracts/api.md` y `quickstart.md`, se
revisan de nuevo los 6 principios: ningún diseño de la Fase 1 introduce una
violación nueva. Las notas a llevar a `/speckit-tasks` explícitamente
son: Principio I (migrar los cuatro ficheros del scorer al repo como prerrequisito),
Principio VI (retirar `guardar.py` por completo al desplegar, sin periodo
de doble escritura), y una nota de alcance: el secreto compartido de
`POST /ingest` (ver `research.md` §4) es una solución mínima válida solo
mientras el único escritor sea el scraper local — el propietario ha
confirmado que quiere usuarios reales en el futuro, momento en el que un
spec propio de autenticación de usuarios deberá sustituir este mecanismo
por completo, no ampliarlo.
