# Contrato del adaptador (Fase 1): `frontend/dashboard/api_datos.py`

El dashboard no expone ninguna interfaz nueva hacia fuera: consume la API de la
spec 001 (`specs/001-backend-api-bbdd/contracts/api.md`). Este contrato fija lo
que ofrece el módulo adaptador a `app.py` y lo que espera de la API.

## Configuración

- Variable de entorno `HOUSESCORE_API_URL` (por defecto `http://127.0.0.1:8000`; no `localhost`, que en Windows añade ~2 s por petición al probar IPv6 primero).
  Se lee en cada llamada, no al importar el módulo, para poder cambiarla en tests.
- Tiempo máximo: 3 s de conexión y 15 s de lectura.

## Funciones

### `obtener_listings(api_url=None) -> pandas.DataFrame`

Pide `GET {api_url}/listings?incluir_retirados=true` y devuelve el DataFrame con
las columnas de `data-model.md`. Lista vacía → `DataFrame` vacío.

### `obtener_historico(api_url=None) -> pandas.DataFrame`

Pide `GET {api_url}/historico` y devuelve el DataFrame con las columnas de
`data-model.md`, ordenado por `fecha`. Lista vacía → `DataFrame` vacío.

### `listings_a_dataframe(items: list[dict]) -> DataFrame` y `historico_a_dataframe(filas: list[dict]) -> DataFrame`

Traducción pura (sin red), para probarla de forma aislada.

### `ApiNoDisponible(Exception)`

Atributos: `mensaje` (texto para el usuario) y `url` (la consultada). Se lanza
en estos casos:

| Situación | `mensaje` |
|---|---|
| No se puede conectar | "No se puede conectar con la API" |
| Tiempo agotado | "La API no ha respondido a tiempo" |
| HTTP 429 | "La API ha limitado las peticiones; espera un momento y recarga" |
| Otro HTTP ≠ 200 | "La API ha devuelto un error (HTTP N)" |
| Cuerpo ilegible o que no es una lista | "La respuesta de la API no es válida" |

No hay reintentos automáticos ni caché propia: la caché es la de Streamlit
(`ttl=30`) y no cachea excepciones.

## Comportamiento de `app.py`

- Carga inicial de listings falla → `st.error` con `mensaje` y `url`, más una
  indicación de cómo arrancar la API, y `st.stop()`. **No se muestra ninguna
  cifra ni tabla.**
- Listings vacíos → mensaje de "sin datos" distinto del anterior.
- Histórico falla → `st.warning` en su sección; el resto de la app sigue.
- Pie de página: muestra la dirección de la API, no una ruta de ficheros.

## Lo que se espera de la API

Los endpoints y campos de la spec 001, tal como están implementados: lectura
pública sin cabeceras especiales; `detalle` como objeto (puede ser `{}`);
`score` y `m2` pueden ser `null`.
