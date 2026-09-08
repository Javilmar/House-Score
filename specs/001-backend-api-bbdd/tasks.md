---

description: "Lista de tareas: Backend (API + Base de Datos) para HouseScore"
---

# Tareas: Backend (API + Base de Datos) para HouseScore

**Entrada**: Documentos de diseño en `specs/001-backend-api-bbdd/`

**Prerrequisitos**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/api.md](contracts/api.md), [quickstart.md](quickstart.md)

**Tests**: Obligatorios en todo el trabajo no trivial — Principio IV de la constitución (TDD, NO NEGOCIABLE). Cada tarea de comportamiento lleva su test antes que la implementación.

**Organización**: Las tareas se agrupan por historia de usuario (US1, US2, US3 de [spec.md](spec.md)) para poder implementar y testear cada una de forma independiente.

## Formato: `[ID] [P?] [Story] Descripción`

- **[P]**: Se puede ejecutar en paralelo (ficheros distintos, sin dependencias)
- **[Story]**: A qué historia de usuario pertenece (US1, US2, US3)
- Todas las rutas son relativas a la raíz del repositorio

## Convenciones de rutas

Según `plan.md` > Estructura del Proyecto: todo el código nuevo vive bajo `backend/` (ya reservado en la raíz del monorepo). El front (`frontend/`) no se toca.

---

## Fase 1: Configuración

**Propósito**: Inicialización del proyecto backend

- [ ] T001 Crear la estructura de directorios de `backend/` (`app/api/`, `app/models/`, `app/db/`, `app/core/`, `worker/scraper/`, `tests/contract/`, `tests/integration/`, `tests/unit/`, `alembic/`) según `plan.md` > Estructura del Proyecto
- [ ] T002 Inicializar el proyecto Python 3.11 en `backend/pyproject.toml` con las dependencias decididas en `research.md`: fastapi, uvicorn, sqlalchemy, alembic, pydantic, slowapi, psycopg, pytest, httpx
- [ ] T003 [P] Configurar linting/formato (ruff) en `backend/pyproject.toml`
- [ ] T004 [P] Escribir `backend/Dockerfile` (build de la imagen usada tanto por `api` como por `worker`, per `research.md` §6)
- [ ] T005 Escribir `backend/docker-compose.yml` con los servicios `api`, `db` (`postgres:16`) y `worker`, per `research.md` §6

---

## Fase 2: Fundacional (Prerrequisitos bloqueantes)

**Propósito**: Base de datos, modelos y configuración compartida que TODAS las historias necesitan

**⚠️ CRÍTICO**: Ninguna historia de usuario puede empezar hasta que esta fase esté completa

- [ ] T006 Configurar el engine y la sesión de SQLAlchemy en `backend/app/db/session.py`, leyendo `DATABASE_URL` de entorno
- [ ] T007 Inicializar Alembic en `backend/alembic/` apuntando a los modelos de `backend/app/models/`
- [ ] T008 [P] Crear el modelo `Listing` en `backend/app/models/listing.py` con los campos y reglas de `data-model.md` § Listing: `url` único no nulo (clave de deduplicación), `m2` nullable (si es `null` ⇒ `datos_insuficientes=true` y `score=null`), `estado` enum (`activo`/`retirado`), `municipio` no nulo
- [ ] T009 [P] Crear el modelo `HistorialPrecio` en `backend/app/models/historial_precio.py` con FK a `Listing`, per `data-model.md` § HistorialPrecio
- [ ] T010 [P] Crear el modelo `PasadaDiaria` en `backend/app/models/pasada_diaria.py` con `fecha` única, per `data-model.md` § PasadaDiaria
- [ ] T011 [P] Crear el modelo `PrecioReferencia` en `backend/app/models/precio_referencia.py` con `municipio` único, per `data-model.md` § PrecioReferencia
- [ ] T012 Generar la migración Alembic inicial para las 4 tablas anteriores en `backend/alembic/versions/`
- [ ] T013 Configurar rate limiting por IP con `slowapi` en `backend/app/core/rate_limit.py`, para aplicarlo a los endpoints de lectura (FR-012)
- [ ] T014 Configurar logging estructurado en `backend/app/core/logging.py` que registre cualquier fallo de ingesta de forma consultable (FR-014) — sin notificación activa, per la clarificación del spec
- [ ] T015 Configurar la carga del secreto compartido (`INGEST_SECRET`) desde variables de entorno en `backend/app/core/config.py`, per `research.md` §4
- [ ] T016 Crear la app FastAPI base en `backend/app/main.py`, montando routers vacíos para `listings`, `historico` e `ingest`

**Punto de control**: Fundación lista — puede empezar la implementación de las historias de usuario.

---

## Fase 3: Historia de Usuario 1 - El front deja de depender de ficheros commiteados (Prioridad: P1) 🎯 MVP (parte 1)

**Objetivo**: La API sirve los listings vigentes y el histórico agregado, ya puntuados, migrando los datos existentes.

**Test independiente**: pedir a la API los listings de una zona y comprobar que la respuesta trae score y `datos_insuficientes`, sin tocar `frontend/datos/`.

### Tests de la Historia de Usuario 1

> **Escribe estos tests PRIMERO, asegúrate de que FALLAN antes de implementar**

- [ ] T017 [P] [US1] Test de contrato para `GET /listings` en `backend/tests/contract/test_listings_get.py`: verifica que cada listing devuelto trae `score` y `datos_insuficientes` (per `contracts/api.md`)
- [ ] T018 [P] [US1] Test de contrato para `GET /historico` en `backend/tests/contract/test_historico_get.py`: verifica el shape de `contracts/api.md` (`fecha`, `total_listings`, `score_medio`, `precio_medio`)
- [ ] T019 [P] [US1] Test unitario: un listing sin `m2` queda marcado `datos_insuficientes=true` y con `score=null` en `backend/tests/unit/test_datos_insuficientes.py` (FR-005)

### Implementación de la Historia de Usuario 1

- [ ] T020 [US1] Implementar `GET /listings` en `backend/app/api/routes_listings.py` con filtros `municipio` e `incluir_retirados` (depende de T008)
- [ ] T021 [US1] Implementar `GET /historico` en `backend/app/api/routes_listings.py` con filtros `desde`/`hasta` (depende de T010)
- [ ] T022 [US1] Aplicar el rate limiting de T013 a ambos endpoints de lectura (FR-012)
- [ ] T023 [US1] Escribir el script de migración one-off `backend/scripts/migrar_datos_existentes.py` que carga `frontend/datos/listings.json`, `frontend/datos/historico_diario.json` y `frontend/config/precios_referencia.json` en las tablas correspondientes, sin pérdida de datos (SC-004)

**Punto de control**: `GET /listings` y `GET /historico` devuelven los datos reales migrados, con rate limiting activo.

---

## Fase 4: Historia de Usuario 2 - Cada pasada del scraper queda disponible sin intervención manual (Prioridad: P1) 🎯 MVP (parte 2)

**Objetivo**: El worker del scraper guarda cada pasada llamando a `POST /ingest`, sin `git push`.

**Test independiente**: enviar una pasada de ejemplo a `POST /ingest` y comprobar que aparece en `GET /listings` inmediatamente, sin ningún paso de git.

### Tests de la Historia de Usuario 2

> **Escribe estos tests PRIMERO, asegúrate de que FALLAN antes de implementar**

- [ ] T024 [P] [US2] Test de contrato: `POST /ingest` con secreto correcto devuelve `201` y el resumen de la pasada, en `backend/tests/contract/test_ingest_post.py`
- [ ] T025 [P] [US2] Test de contrato: `POST /ingest` sin cabecera `Authorization` o con secreto incorrecto devuelve `401`, en `backend/tests/contract/test_ingest_auth.py` (FR-010/FR-011)
- [ ] T026 [P] [US2] Test de integración: enviar la misma pasada dos veces no crea listings duplicados (dedupe por `url`), en `backend/tests/integration/test_ingest_dedupe.py` (FR-009/SC-005)
- [ ] T027 [P] [US2] Test de integración: una bajada de precio >40% en una pasada queda como candidata y no se confirma hasta la siguiente pasada similar, en `backend/tests/integration/test_price_drop.py` (regla `OUTLIER_DROP_RATIO` migrada de `listings_store.py`)
- [ ] T028 [P] [US2] Test de integración: un listing de un municipio bloqueado de Toledo Norte se descarta antes de persistir, en `backend/tests/integration/test_municipios_bloqueados.py` (FR-006)
- [ ] T029 [P] [US2] Test de integración: un listing activo sin aparecer en 7 días pasa a `retirado`, en `backend/tests/integration/test_delisted.py` (FR-007)

### Implementación de la Historia de Usuario 2

- [ ] T030 [US2] Implementar la verificación del secreto compartido (cabecera `Authorization: Bearer`) en `backend/app/api/routes_ingest.py` (depende de T015)
- [ ] T031 [US2] Implementar la deduplicación por `url` en `backend/app/services/ingest_service.py` (depende de T008)
- [ ] T032 [US2] Implementar la regla de historial de precio / precio candidato en `backend/app/services/ingest_service.py` (depende de T009, T031)
- [ ] T033 [US2] Migrar a `backend/app/services/ingest_service.py` la lista de municipios bloqueados de Toledo Norte actualmente en `frontend/dashboard/guardar.py` (`_TOLEDO_NORTE_BLOQUEADOS`)
- [ ] T034 [US2] Implementar la detección de listings retirados (umbral 7 días) en `backend/app/services/ingest_service.py` (depende de T031)
- [ ] T035 [US2] Implementar la actualización de `PasadaDiaria` tras cada ingesta en `backend/app/services/ingest_service.py` (depende de T010)
- [ ] T036 [US2] Implementar `POST /ingest` completo en `backend/app/api/routes_ingest.py`, orquestando T031-T035 (depende de T030)
- [ ] T037 [US2] Registrar en el log (T014) cualquier fallo de la ingesta, sin notificación activa (FR-014)
- [ ] T038 [US2] [BLOQUEADA — pendiente de que el propietario aporte el fichero] Incorporar `property_scorer.py` a `backend/worker/scraper/property_scorer.py`
- [ ] T039 [US2] Implementar el cliente HTTP del worker que llama a `POST /ingest` con el secreto compartido, en `backend/worker/scraper/client.py` (depende de T038)
- [ ] T040 [US2] Configurar el comando de arranque del worker en `backend/docker-compose.yml` y documentar su despliegue como Background Worker de Render (depende de T039)

**Punto de control**: MVP completo — el front puede leer de la API (US1) y el worker puede escribir en ella sin git (US2).

---

## Fase 5: Historia de Usuario 3 - Entorno local reproducible (Prioridad: P2)

**Objetivo**: Levantar el backend completo en local con un único comando.

**Test independiente**: en un checkout limpio, `docker compose up --build` deja todo operativo sin pasos manuales.

### Tests de la Historia de Usuario 3

- [ ] T041 [P] [US3] Test de integración: tras `docker compose up`, la API responde en `backend/tests/integration/test_entorno_local.py` (valida el Escenario 1 de `quickstart.md`)

### Implementación de la Historia de Usuario 3

- [ ] T042 [US3] Configurar que las migraciones de Alembic corran automáticamente al arrancar el contenedor `api` (`backend/entrypoint.sh`) (depende de T012)
- [ ] T043 [US3] Verificar y documentar en `backend/README.md` el arranque con un único comando en menos de 5 minutos (SC-003), contra el Escenario 1 de `quickstart.md` (depende de T005, T042)
- [ ] T044 [US3] Configurar `docker compose run --rm api pytest` para ejecutar toda la suite contra el entorno local sin tocar datos de producción (depende de T002)

**Punto de control**: Cualquiera puede clonar el repo y tener el backend funcionando en local sin pasos manuales.

---

## Fase Final: Pulido y aspectos transversales

- [ ] T045 [P] Documentar las variables de entorno (`INGEST_SECRET`, `DATABASE_URL`, etc.) en `backend/README.md`
- [ ] T046 [P] Test de integración de rate limiting: verificar que se devuelve `429` al superar el límite, en `backend/tests/integration/test_rate_limiting.py` (Escenario 5 de `quickstart.md`, FR-012)
- [ ] T047 Ejecutar los 5 escenarios de `quickstart.md` de principio a fin antes de desplegar a producción
- [ ] T048 Configurar el despliegue en Render: Web Service (`api`), Background Worker (`worker`), PostgreSQL gestionado, variables de entorno (`INGEST_SECRET`, `DATABASE_URL`)
- [ ] T049 Retirar por completo `frontend/dashboard/guardar.py` y su flujo de `git push` una vez el backend esté en producción y el worker funcionando — sin periodo de doble escritura (Principio VI, corte duro)

---

## Dependencias y orden de ejecución

### Dependencias entre fases

- **Configuración (Fase 1)**: sin dependencias, empieza de inmediato
- **Fundacional (Fase 2)**: depende de Configuración — BLOQUEA todas las historias de usuario
- **US1 (Fase 3)** y **US2 (Fase 4)**: ambas dependen solo de Fundacional; forman juntas el MVP (Historia 1 = lectura, Historia 2 = escritura) y pueden avanzar en paralelo entre sí, aunque T038-T040 de US2 quedan bloqueadas hasta recibir `property_scorer.py`
- **US3 (Fase 5)**: depende de Fundacional; en la práctica conviene tenerla lista pronto porque US1/US2 se testean mejor con el entorno local ya reproducible
- **Pulido (Fase Final)**: depende de que US1, US2 y US3 estén completas; T049 depende además de que el despliegue (T048) esté confirmado funcionando

### Bloqueo externo activo

- **T038** está bloqueada: requiere que el propietario suba `property_scorer.py` desde su ordenador. T039 y T040 dependen de T038. El resto del backend (Fases 1-3, y la mayor parte de la Fase 4 y 5) no depende de este fichero y puede implementarse y testearse igualmente.

### Dentro de cada historia de usuario

- Tests escritos y en rojo antes que la implementación (Principio IV)
- Modelos (Fase 2) antes que servicios
- Servicios antes que endpoints
- T049 (retirar `guardar.py`) es literalmente el último paso, tras confirmar que todo lo demás funciona en producción

### Oportunidades de paralelización

- T003, T004 en paralelo tras T002
- T008-T011 (los 4 modelos) en paralelo entre sí
- T017-T019 (tests de US1) en paralelo entre sí
- T024-T029 (tests de US2) en paralelo entre sí
- US1 (Fase 3) y US3 (Fase 5) pueden avanzar en paralelo con US2 (Fase 4), salvo por T038-T040

---

## Ejemplo de paralelización: Fase 2 (modelos)

```bash
Task: "Crear el modelo Listing en backend/app/models/listing.py"
Task: "Crear el modelo HistorialPrecio en backend/app/models/historial_precio.py"
Task: "Crear el modelo PasadaDiaria en backend/app/models/pasada_diaria.py"
Task: "Crear el modelo PrecioReferencia en backend/app/models/precio_referencia.py"
```

---

## Estrategia de implementación

### MVP primero (US1 + US2)

1. Completar Fase 1: Configuración
2. Completar Fase 2: Fundacional (crítico — bloquea todo)
3. Completar Fase 3 (US1) y Fase 4 (US2) — juntas forman el MVP funcional (lectura + escritura sin JSON/git)
4. **PARAR Y VALIDAR**: ejecutar los Escenarios 1 y 2 de `quickstart.md`
5. Nota: T038-T040 pueden quedar pendientes del fichero del propietario sin bloquear la validación del resto del MVP con datos de prueba

### Entrega incremental

1. Fundación lista → Fase 3 (US1): la API ya sirve datos migrados → validar Escenario 1
2. Fase 4 (US2, sin T038-T040): la ingesta funciona con datos de prueba → validar Escenarios 2 y 3
3. Al recibir `property_scorer.py`: completar T038-T040 → el worker real sustituye a los datos de prueba
4. Fase 5 (US3): entorno local reproducible confirmado → validar Escenario 1 de quickstart en limpio
5. Fase Final: rate limiting, despliegue a Render, y solo entonces T049 (retirar `guardar.py`)

---

## Notas

- [P] = ficheros distintos, sin dependencias entre sí
- [US1]/[US2]/[US3] traza cada tarea a su historia de usuario en `spec.md`
- Todo comportamiento nuevo lleva su test en rojo antes que la implementación (Principio IV, no negociable)
- T038 es un bloqueo externo real, no una tarea que se pueda "hacer trampa" y saltarse — el resto del plan está diseñado para no depender de ella
- Tras cada tarea o grupo lógico, commit siguiendo la cadena de Spec Kit
