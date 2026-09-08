# Plan de Implementación: Backend (API + Base de Datos) para HouseScore

**Rama**: `001-backend-api-bbdd` | **Fecha**: 2026-09-08 | **Spec**: [spec.md](spec.md)

**Entrada**: Especificación de la funcionalidad en `specs/001-backend-api-bbdd/spec.md`

## Resumen

Sustituir el flujo actual de HouseScore (scraper local → `guardar.py` →
JSON commiteado en `frontend/datos/` → Streamlit lee el repo) por un backend
con API + base de datos: una API FastAPI que sirve los listings ya
puntuados y el histórico agregado, y un worker (el propio scraper,
migrado desde fuera del repo) que escribe cada pasada llamando a un
endpoint de ingesta de esa misma API. Todo se despliega en Render
(Web Service para la API, Background Worker para el scraper, PostgreSQL
gestionado), con un `docker-compose` para poder levantarlo todo en local
con un único comando. El front (Streamlit) no se toca en este plan.

## Contexto Técnico

**Lenguaje/Versión**: Python 3.11 (coincide con el `devcontainer` actual y
con el resto del código Python del proyecto)

**Dependencias principales**: FastAPI, Uvicorn, SQLAlchemy 2.x, Alembic,
Pydantic, slowapi (rate limiting), psycopg (driver PostgreSQL), pytest,
httpx (cliente de test para FastAPI)

**Almacenamiento**: PostgreSQL 16 (instancia gestionada de Render en
producción; contenedor Postgres oficial en `docker-compose` para local)

**Testing**: pytest + `httpx.AsyncClient`/`TestClient` de FastAPI, siguiendo
TDD (Principio IV de la constitución): tests de contrato para cada
endpoint, tests de integración para el flujo worker→API→BBDD, tests
unitarios para las reglas de negocio migradas de `listings_store.py`

**Plataforma objetivo**: contenedores Linux en Render (Web Service +
Background Worker + PostgreSQL gestionado); local vía Docker Compose

**Tipo de proyecto**: web-service (API) + worker (proceso en segundo plano)
— dos artefactos desplegables que comparten la misma base de datos

**Objetivos de rendimiento**: sin exigencias de alto rendimiento — un único
usuario real, unos pocos cientos de listings vigentes (≈500, según el
volumen actual de `frontend/datos/listings.json`). El objetivo es
disponibilidad y consistencia, no throughput.

**Restricciones**:
- El endpoint de ingesta (escritura) no debe ser invocable por nadie salvo
  el worker del scraper (FR-011) — ver nota de Render en Constitution Check.
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
| I. Motor de scoring como única fuente de verdad | **PASS, con nota.** El motor de scoring (`property_scorer.py`) no se reimplementa: se migra tal cual como parte del worker. **Hallazgo importante**: hoy ese script vive fuera de este repositorio, en el ordenador del propietario (`~/AppData/Local/hermes/scripts/property_scorer.py`), no está en git. Traerlo al repo (bajo `backend/worker/`) es un prerrequisito de esta implementación — se refleja como tarea explícita en `/speckit-tasks`, no como una violación del principio. |
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
│   └── scraper/                 # property_scorer.py migrado + cliente que llama a POST /ingest
├── tests/
│   ├── contract/                # un test por endpoint público/de ingesta
│   ├── integration/              # flujo worker → API → BBDD de extremo a extremo
│   └── unit/                     # reglas migradas de listings_store.py (price_drop, dedupe, delisted...)
├── alembic/                      # migraciones versionadas
├── Dockerfile
├── docker-compose.yml            # api + postgres + worker, para desarrollo local
└── requirements.txt / pyproject.toml

frontend/        # sin cambios en este plan
```

**Decisión de estructura**: se usa `backend/` (ya reservado en la raíz del
monorepo, ver README.md) como único proyecto, con dos puntos de entrada
(`app/main.py` para la API, `worker/scraper/` para el worker) que comparten
`app/models/` y `app/db/`. No se crean paquetes ni repos separados para API
y worker — es innecesario a esta escala y complicaría compartir el modelo
de datos entre ambos.

## Complexity Tracking

*Sin violaciones que justificar.*

## Re-chequeo de Constitution Check (post-Fase 1)

Tras diseñar `data-model.md`, `contracts/api.md` y `quickstart.md`, se
revisan de nuevo los 6 principios: ningún diseño de la Fase 1 introduce una
violación nueva. Las notas a llevar a `/speckit-tasks` explícitamente
son: Principio I (migrar `property_scorer.py` al repo como prerrequisito),
Principio VI (retirar `guardar.py` por completo al desplegar, sin periodo
de doble escritura), y una nota de alcance: el secreto compartido de
`POST /ingest` (ver `research.md` §4) es una solución mínima válida solo
mientras el único escritor sea el worker del scraper — el propietario ha
confirmado que quiere usuarios reales en el futuro, momento en el que un
spec propio de autenticación de usuarios deberá sustituir este mecanismo
por completo, no ampliarlo.
