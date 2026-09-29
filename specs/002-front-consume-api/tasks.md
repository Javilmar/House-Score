---

description: "Lista de tareas: El dashboard consume la API"
---

# Tareas: El dashboard consume la API

**Entrada**: Documentos de diseño en `specs/002-front-consume-api/`

**Prerrequisitos**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/api-datos.md](contracts/api-datos.md), [quickstart.md](quickstart.md)

**Tests**: Obligatorios (Principio IV, TDD, NO NEGOCIABLE): cada tarea de comportamiento lleva su test antes que la implementación, y el test debe fallar primero.

**Organización**: Por historia de usuario (US1, US2, US3 de [spec.md](spec.md)).

## Formato: `[ID] [P?] [Story] Descripción`

- **[P]**: Se puede ejecutar en paralelo (ficheros distintos, sin dependencias)
- **[Story]**: A qué historia de usuario pertenece
- Rutas relativas a la raíz del repositorio

## Convenciones de rutas

Todo el código nuevo vive en `frontend/dashboard/` (junto a `app.py`) y sus tests en `frontend/dashboard/tests/`. El resto de `app.py` no se toca. Los tests se ejecutan con `python -m pytest frontend/dashboard/tests -q`.

---

## Fase 1: Configuración

- [ ] T001 Declarar `requests` en `frontend/requirements.txt` (ya viene con Streamlit como dependencia transitiva; se fija la versión instalada, `requests==2.34.2`)
- [ ] T002 [P] Escribir la API falsa de los tests en `frontend/dashboard/tests/fake_api.py`: un `http.server.ThreadingHTTPServer` en un hilo, puerto libre, que sirve `GET /listings` y `GET /historico` con JSON configurable, y permite forzar estado HTTP, cuerpo inválido y retardo; con una fábrica de datos de ejemplo en el formato del contrato de `specs/001-backend-api-bbdd/contracts/api.md` (incluye un listing retirado, uno con `datos_insuficientes` y `score` nulo, y otro con `detalle` vacío)

---

## Fase 2: Fundacional

**⚠️ CRÍTICO**: bloquea todas las historias.

- [ ] T003 Crear `frontend/dashboard/api_datos.py` con la excepción `ApiNoDisponible(mensaje, url)` (atributos `mensaje` y `url`, per `contracts/api-datos.md`) y las firmas vacías de `listings_a_dataframe`, `historico_a_dataframe`, `obtener_listings` y `obtener_historico`

**Punto de control**: el módulo importa; los tests de las historias pueden escribirse contra él.

---

## Fase 3: Historia de Usuario 1 - El dashboard muestra los datos vivos de la API (Prioridad: P1) 🎯 MVP

**Objetivo**: el dashboard muestra lo mismo que hoy con datos de la API, sin leer ficheros del repo.

**Test independiente**: con la API falsa (o la real) en marcha, la app arranca sin excepciones y KPIs, tablas y gráficos reflejan los datos servidos.

### Tests de la Historia de Usuario 1

> **Escribe estos tests PRIMERO y asegúrate de que FALLAN antes de implementar**

- [ ] T004 [P] [US1] Tests de `listings_a_dataframe` en `frontend/dashboard/tests/test_api_datos.py`: mapeo de columnas de `data-model.md` (`titulo→title`, `precio→price`, `habitaciones→rooms`, `banos→bathrooms`, `fuente→source`, `bajada_precio→price_drop`, `precio_anterior→previous_price`, `primera_aparicion→first_seen` y `ultima_aparicion→last_seen` como `Timestamp`); `estado` `activo`→`active` y `retirado`→`delisted`; `detalle.*` volcado como columnas (`location`, `description`, `score_details`, `features`, ...); una clave de `detalle` no pisa una columna principal; `detalle` vacío no rompe; `m2` y `score` nulos quedan `NaN`; lista vacía → `DataFrame` vacío; orden por `score` descendente con `NaN` al final
- [ ] T005 [P] [US1] Tests de `historico_a_dataframe` en `frontend/dashboard/tests/test_api_datos.py`: `total_listings→count`, `score_medio→avg_score`, `precio_medio→avg_price`, `precio_min→min_price`, `precio_max→max_price`, `fecha` como `Timestamp`, orden ascendente, lista vacía → `DataFrame` vacío
- [ ] T006 [P] [US1] Tests de `obtener_listings` y `obtener_historico` contra la API falsa en `frontend/dashboard/tests/test_api_datos.py`: `obtener_listings` pide `GET /listings?incluir_retirados=true` y devuelve el `DataFrame` traducido; `obtener_historico` pide `GET /historico`
- [ ] T007 [P] [US1] Test de la app completa en `frontend/dashboard/tests/test_app_api.py` con `streamlit.testing.v1.AppTest.from_file("frontend/dashboard/app.py")` y `HOUSESCORE_API_URL` apuntando a la API falsa: la app arranca sin excepciones, aparece el título `House Score`, hay KPIs y tablas, y los listings retirados y sin valorar no rompen la pantalla; el test no debe leer ni depender de `frontend/datos/`

### Implementación de la Historia de Usuario 1

- [ ] T008 [US1] Implementar `listings_a_dataframe` en `frontend/dashboard/api_datos.py` según `data-model.md` (lista de diccionarios en una sola pasada, sin `json_normalize`; conversión numérica y de fechas idéntica a la de `cargar_datos()` actual)
- [ ] T009 [US1] Implementar `historico_a_dataframe` en `frontend/dashboard/api_datos.py` según `data-model.md`
- [ ] T010 [US1] Implementar `obtener_listings` y `obtener_historico` en `frontend/dashboard/api_datos.py` con `requests` (`timeout=(3, 15)`) y la dirección por defecto `http://localhost:8000` (depende de T008, T009)
- [ ] T011 [US1] En `frontend/dashboard/app.py`, hacer que `cargar_datos()` y `cargar_historico()` (conservando `@st.cache_data(ttl=30)`) devuelvan `api_datos.obtener_listings()` y `api_datos.obtener_historico()`, y eliminar la lectura de `listings.json` e `historico_diario.json` y de `DATA_DIR` (FR-001, FR-009); el resto de `app.py` no se toca (depende de T010)

**Punto de control**: la app muestra los datos de la API y no lee ficheros del repo.

---

## Fase 4: Historia de Usuario 2 - Aviso claro si la API no responde (Prioridad: P1)

**Objetivo**: con la API caída o rota, aviso explícito y ninguna cifra vieja.

**Test independiente**: parar la API falsa, abrir la app y ver el aviso sin tablas; volver a arrancarla y recuperar al recargar.

### Tests de la Historia de Usuario 2

> **Escribe estos tests PRIMERO y asegúrate de que FALLAN antes de implementar**

- [ ] T012 [P] [US2] Tests de errores de red en `frontend/dashboard/tests/test_api_datos.py` contra la API falsa: conexión rechazada (puerto sin servidor), tiempo agotado (retardo mayor que el timeout), HTTP 429, HTTP 500, cuerpo que no es JSON y cuerpo JSON que no es una lista → cada uno lanza `ApiNoDisponible` con el `mensaje` de `contracts/api-datos.md` y la `url` consultada; el 429 no se reintenta (una sola petición)
- [ ] T013 [P] [US2] Tests de la app en `frontend/dashboard/tests/test_app_api.py`: con la API caída aparece un `st.error` con la dirección consultada y no hay KPIs (`st.metric`) ni tablas de datos; con la API respondiendo `[]` aparece el mensaje de "sin datos", distinto del de API caída; si la API falla solo en `/historico`, el resto de la app se muestra y en su sección hay un `st.warning`; tras volver a responder la API y volver a ejecutar la app, se muestran los datos sin reiniciar

### Implementación de la Historia de Usuario 2

- [ ] T014 [US2] En `frontend/dashboard/api_datos.py`, convertir todos los fallos de `requests` y de formato en `ApiNoDisponible` con los mensajes de `contracts/api-datos.md` (conexión, tiempo agotado, 429, HTTP ≠ 200, cuerpo no válido), sin reintentos ni caché propia (FR-005, FR-012)
- [ ] T015 [US2] En `frontend/dashboard/app.py` (carga inicial, donde hoy está `df = cargar_datos()`), capturar `ApiNoDisponible` → `st.error` con `mensaje` y `url` más cómo arrancar la API (`cd backend && docker compose up -d`) y `st.stop()`; y capturarla en el bloque del gráfico de evolución con `st.warning` en su sección (FR-005, FR-007)
- [ ] T016 [US2] En `frontend/dashboard/app.py`, sustituir el aviso de "No hay datos todavía" (instrucciones de `property_scorer.py` y `guardar.py`) por uno que distinga API vacía de API caída e indique ejecutar el scorer del repo (`backend/worker/scraper/property_scorer_all.py`) (FR-006, FR-011)

**Punto de control**: con la API caída no se muestra ninguna cifra; se recupera al recargar.

---

## Fase 5: Historia de Usuario 3 - Configurar dónde está la API (Prioridad: P2)

**Objetivo**: la dirección de la API se configura con una variable de entorno.

**Test independiente**: sin variable, consulta la dirección local; con ella, la indicada.

### Tests de la Historia de Usuario 3

> **Escribe estos tests PRIMERO y asegúrate de que FALLAN antes de implementar**

- [ ] T017 [P] [US3] Tests en `frontend/dashboard/tests/test_api_datos.py`: sin `HOUSESCORE_API_URL` se consulta `http://localhost:8000`; con la variable (puesta con `monkeypatch`/`mock.patch.dict` después de importar el módulo) se consulta esa dirección; el `mensaje` de error incluye la dirección configurada
- [ ] T018 [P] [US3] Test en `frontend/dashboard/tests/test_app_api.py`: el pie de página de la app muestra la dirección de la API y ya no muestra rutas de ficheros ni `property_scorer.py`

### Implementación de la Historia de Usuario 3

- [ ] T019 [US3] En `frontend/dashboard/api_datos.py`, leer `HOUSESCORE_API_URL` en cada llamada (no al importar) con `http://localhost:8000` por defecto, y usarla en las peticiones y en `ApiNoDisponible.url` (FR-008)
- [ ] T020 [US3] En `frontend/dashboard/app.py`, sustituir el pie de página `Datos en {DATA_DIR}` y el texto `Scraper: property_scorer.py ...` por la dirección de la API y el scorer actual (FR-011)

**Punto de control**: la dirección es configurable y aparece en el pie y en los avisos.

---

## Fase Final: Pulido y aspectos transversales

- [ ] T021 Ejecutar la suite completa `python -m pytest frontend/dashboard/tests -q` y comprobar que sigue pasando `test_listings_store.py` (se retira con T052 de la spec 001)
- [ ] T022 Validar `quickstart.md` contra la API real de Docker con los ~2.000 listings: Escenarios 1 a 5 (datos del último día, `grep` sin lecturas de ficheros, API parada y recuperación, dirección configurable, primera carga < 5 s)
- [ ] T023 [P] Actualizar `frontend/dashboard/FUNCIONALIDADES.md` (diagrama y descripción del flujo de datos: ya no es `guardar.py → datos/*.json → app.py`, sino scorer → API → `app.py`) y añadir cómo arrancar el dashboard a `backend/README.md`
- [ ] T024 [P] En `specs/001-backend-api-bbdd/tasks.md`, anotar en T052 que el dashboard ya no lee `frontend/datos/` (queda por retirar `guardar.py`, `listings_store.py`, su test y los JSON)

---

## Dependencias y orden de ejecución

- **Configuración (Fase 1)** → **Fundacional (Fase 2)** → historias.
- **US1 (P1)** primero: es el MVP. **US2 (P1)** y **US3 (P2)** dependen de `api_datos.py` (T003, T010) y de `app.py` (T011), y se hacen en ese orden: US2 antes de US3 porque el aviso de error necesita ya la dirección por defecto.
- **Pulido** al final.
- Dentro de cada historia: tests en rojo, después implementación (Principio IV).
- Tareas que tocan `frontend/dashboard/app.py` (T011, T015, T016, T020) y `test_api_datos.py`/`test_app_api.py` se hacen en secuencia (mismo fichero).

### Oportunidades de paralelización

- T001 y T002 en paralelo.
- T004-T007 (tests de US1) en paralelo entre sí salvo por compartir fichero (`test_api_datos.py` y `test_app_api.py`); T004-T006 van juntos en un mismo fichero.
- T023 y T024 en paralelo.

## Estrategia de implementación

1. Fases 1 y 2.
2. US1 (MVP): tests en rojo, traducción y carga, `app.py` cargando de la API. **Parar y validar** con la API falsa.
3. US2: errores y avisos. Validar con la API parada.
4. US3: variable de entorno y pie de página.
5. Pulido y validación con la API real de Docker.

## Notas

- La spec 001 tiene la API en `127.0.0.1:8000` con `restart: unless-stopped`.
- El despliegue del dashboard en la nube queda fuera (necesita el túnel, T050 de la spec 001).
- Retirar `guardar.py`, `listings_store.py` y `frontend/datos/` NO es parte de esta spec (T052 de la 001).
- Tras cada tarea o grupo lógico, commit siguiendo la cadena de Spec Kit.
