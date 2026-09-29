# Investigación (Fase 0): El dashboard consume la API

## 1. Qué lee hoy el dashboard

**Hallazgo**: `app.py` solo lee del repositorio dos ficheros, en `cargar_datos()`
(línea ~552, `listings.json`) y `cargar_historico()` (~591,
`historico_diario.json`), ambas con `@st.cache_data(ttl=30)`. No lee
`config/precios_referencia.json` (lo usa el scorer). El mapa
`assets/municipios_zona.geojson` es un recurso estático propio y no cambia.

Columnas que usa el resto de la app (a partir de `row.get(...)` y `df[...]`):
`title, description, location, price, url, score, m2, eur_m2, source, rooms,
bathrooms, first_seen, last_seen, year_built, status, price_drop,
previous_price, features, energy_rating, datos_insuficientes, municipio`, y
`score_details` (desglose). En el histórico: `fecha, count, avg_price,
avg_score, min_price, max_price`.

`app.py` también deriva la zona (`zona(location, title, description)`) y el
municipio (`municipio` o el texto entre paréntesis de `location`), así que
`location` y `municipio` deben conservarse.

**Consecuencia**: la traducción de la API al formato actual cabe en un adaptador
de una sola función por endpoint; el resto de la app no necesita cambios.

## 2. Cliente HTTP

**Decisión**: `requests`, con `timeout=(3, 15)` (conexión, lectura).

**Motivo**: ya viene instalado con Streamlit (dependencia transitiva), es
síncrono y basta para una petición por carga; se declara en
`frontend/requirements.txt` para no depender de algo transitivo.

**Alternativas consideradas**:
- *httpx*: válido, pero añade una dependencia que el dashboard no tiene.
- *urllib (stdlib)*: sin dependencias, pero más código para errores y JSON.

## 3. Dónde y cómo tratar los errores

**Decisión**: `api_datos` lanza `ApiNoDisponible(mensaje, url)` para: error de
conexión, tiempo agotado, HTTP ≠ 200 (con mensaje específico para 429) y JSON
ilegible o con forma inesperada. `app.py` captura la excepción en el punto de
carga inicial: `st.error(...)` con el mensaje y la URL consultada, y
`st.stop()`. Si solo falla el histórico, se muestra `st.warning` dentro de la
sección del gráfico y el resto sigue funcionando.

**Motivo**: `st.cache_data` no cachea las excepciones, así que la siguiente
recarga vuelve a intentarlo sin reiniciar (FR-007). Una sola petición por
carga y sin bucles de reintento evita chocar con el rate limiting (FR-012).

**Alternativas consideradas**:
- *Servir la última respuesta buena en caché si la API cae*: descartado, la
  spec exige no mostrar datos antiguos (FR-005) y el corte duro (Principio VI).
- *Reintentos automáticos con espera*: descartado; una recarga manual basta y
  evita bucles.

## 4. Distinguir "API caída" de "sin listings"

**Decisión**: un 200 con lista vacía devuelve un DataFrame vacío y `app.py`
muestra el mensaje de "sin datos" (con el texto actualizado al flujo nuevo);
todo lo demás es `ApiNoDisponible` (FR-006).

## 5. Valores nulos que antes eran números

**Hallazgo**: en los JSON antiguos "sin m²" era `0` y un listing con datos
insuficientes podía llevar un score numérico. La API sirve `m2 = null` y
`score = null` en esos casos (FR-005 de la spec 001).

**Decisión**: el adaptador no inventa valores: deja `NaN`. `cargar_datos()` ya
convierte con `pd.to_numeric` y ordena con `na_position="last"`; los KPI ya
excluyen `datos_insuficientes` del score medio. Se verifica con un test de la
app completa (AppTest) contra una API falsa que incluye estos casos.

## 6. Cómo probar sin la API real

**Decisión**: una API falsa real (`http.server.ThreadingHTTPServer` en un hilo,
puerto libre) que sirve JSON fijo, para probar el adaptador con HTTP de verdad
(timeouts, 429, JSON roto, caída). Para la app completa, `AppTest.from_file`
de Streamlit con `HOUSESCORE_API_URL` apuntando a esa API falsa: comprueba que
la app arranca sin excepciones, que aparecen las pestañas y KPIs, y que con la
API caída aparece el aviso y ninguna cifra.

**Alternativas consideradas**: *mockear `requests`*: más frágil y no prueba el
HTTP real; *usar la API real*: depende de Docker y de datos que cambian.

## 7. Volumen y rendimiento

**Hallazgo**: `GET /listings?incluir_retirados=true` devuelve ~2.000
listings (hoy ~3 MB con descripciones de hasta 500 caracteres). Con caché de
30 s son como mucho 2 peticiones cada 30 s, muy por debajo del límite de
60/min. SC-004 (< 5 s) se mide en `quickstart.md`.

**Decisión**: construir el DataFrame con una lista de diccionarios (una sola
pasada) y no `json_normalize`, para mantener las columnas iguales a las
actuales sin renombrados posteriores.

## 8. Textos del dashboard

**Hallazgo**: el aviso de "no hay datos" (líneas ~1019-1023) manda ejecutar
`property_scorer.py` y `guardar.py`, y el pie (línea ~2759) dice
`Datos en {DATA_DIR}` y `Scraper: property_scorer.py`. Ninguno vale ya.

**Decisión**: el aviso de sin-datos indica arrancar la API y ejecutar el
scorer del repo (`backend/worker/scraper/property_scorer_all.py`); el pie
muestra la dirección de la API en lugar de `DATA_DIR`. `DATA_DIR` se elimina.

---

Todos los `NEEDS CLARIFICATION` quedan resueltos con las decisiones anteriores.
