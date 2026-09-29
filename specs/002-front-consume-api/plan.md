# Plan de Implementación: El dashboard consume la API

**Rama**: `002-front-consume-api` | **Fecha**: 2026-09-29 | **Spec**: [spec.md](spec.md)

**Entrada**: Especificación de la funcionalidad en `specs/002-front-consume-api/spec.md`

## Resumen

El dashboard de Streamlit deja de leer `frontend/datos/listings.json` y
`historico_diario.json` y pasa a ser cliente de la API del backend (spec 001).
Un único módulo adaptador (`frontend/dashboard/api_datos.py`) pide
`GET /listings?incluir_retirados=true` y `GET /historico`, traduce el contrato
de la API (español, con `detalle`) al formato de columnas que ya usa el resto
de `app.py` (inglés: `title`, `price`, `rooms`, `status`, ...) y lanza una
excepción propia si la API falla. `app.py` solo cambia en sus dos funciones de
carga, en el tratamiento del error (aviso claro + `st.stop()`) y en los textos
que hablaban del flujo antiguo. Corte duro: se elimina la lectura de JSON.

## Contexto Técnico

**Lenguaje/Versión**: Python 3.11 (el mismo del dashboard actual)

**Dependencias principales**: Streamlit 1.58, pandas 3.0, plotly 6.8 (ya
fijadas en `frontend/requirements.txt`) y `requests` para el cliente HTTP
(ya es dependencia transitiva de Streamlit; se declara explícitamente).

**Almacenamiento**: N/A — el dashboard solo lee de la API; no escribe ni
persiste datos.

**Testing**: `unittest` (el estilo de `frontend/dashboard/tests/`) ejecutado
con `pytest`; una API falsa real (`http.server` en un hilo) para los tests del
adaptador, y `streamlit.testing.v1.AppTest` para un test de humo de la app
completa contra esa API falsa.

**Plataforma objetivo**: ejecución local con `streamlit run` en el PC del
propietario, junto a la API (`http://localhost:8000`).

**Tipo de proyecto**: aplicación web de un solo usuario (cliente de la API).

**Objetivos de rendimiento**: primera pantalla en < 5 s con ~2.000 listings
(SC-004); las peticiones se cachean 30 s (`st.cache_data(ttl=30)`, como hoy).

**Restricciones**: sin autenticación (lectura pública); una sola petición por
carga, con tiempo máximo de espera y sin reintentos en bucle (FR-012); el resto
de `app.py` no debe tocarse.

**Escala/Alcance**: ~2.000 listings (activos + retirados), 45+ filas de
histórico, 1 usuario.

## Constitution Check

*GATE: Debe superarse antes de la Fase 0 de investigación. Volver a comprobar tras el diseño de la Fase 1.*

| Principio | Evaluación |
|---|---|
| I. Motor de scoring como única fuente de verdad | **PASS.** El dashboard no recalcula ni fuerza scores: muestra los de la API y trata `score = null`/`datos_insuficientes` como "sin valorar", como hoy. |
| II. Desacoplo front-datos (fases) | **PASS.** Es exactamente la transición Fase 2 → "el front de Streamlit pasa de leer ficheros commiteados a ser cliente de la API", en su propio spec. |
| III. Desarrollo gateado por el harness | **PASS.** Cadena `/speckit-specify → plan → tasks → implement`. |
| IV. Desarrollo guiado por tests | **PASS, exigido.** Tests del adaptador y de la app en rojo antes de implementar. |
| V. Disciplina de alcance | **PASS.** Sin nuevas fuentes, municipios ni funcionalidades de UI: solo cambia el origen de datos. |
| VI. Corte duro sin shims | **PASS.** Se elimina la lectura de los JSON; no hay modo dual ni fallback a ficheros (si la API cae, se avisa; no se sirven datos viejos). |

Ninguna violación requiere justificación en Complexity Tracking.

## Estructura del Proyecto

### Documentación (esta funcionalidad)

```text
specs/002-front-consume-api/
├── plan.md              # Este fichero
├── research.md          # Fase 0
├── data-model.md        # Fase 1 (mapeo API → columnas del dashboard)
├── quickstart.md        # Fase 1
├── contracts/
│   └── api-datos.md     # Fase 1 (contrato del adaptador)
└── tasks.md             # Fase 2 (/speckit-tasks)
```

### Código fuente (raíz del repositorio)

```text
frontend/
├── requirements.txt              # + requests
└── dashboard/
    ├── app.py                    # cargar_datos()/cargar_historico() delegan en api_datos; aviso de error; textos
    ├── api_datos.py              # NUEVO: cliente + traducción API → columnas del dashboard
    └── tests/
        ├── test_listings_store.py   # sin cambios (se retira con T052 de la spec 001)
        ├── test_api_datos.py        # NUEVO: traducción, errores y API falsa
        └── test_app_api.py          # NUEVO: AppTest de la app contra la API falsa
```

**Decisión de estructura**: un solo módulo nuevo junto a `app.py`, sin
paquetes. `app.py` es un script único de ~2.700 líneas; el adaptador concentra
todo el conocimiento del contrato de la API en un punto para no tocar el resto.

## Complexity Tracking

*Sin violaciones que justificar.*

## Re-chequeo de Constitution Check (post-Fase 1)

Tras diseñar el mapeo (`data-model.md`) y el contrato del adaptador
(`contracts/api-datos.md`), los seis principios siguen en PASS. Nota para
`/speckit-tasks`: `guardar.py`, `listings_store.py`, su test y `frontend/datos/`
no se retiran aquí (T052 de la spec 001), aunque tras este cambio el dashboard
ya no los use.
