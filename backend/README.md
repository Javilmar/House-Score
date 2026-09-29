# Backend de HouseScore

API (FastAPI) + base de datos (PostgreSQL) que sustituyen el flujo de JSON commiteados en
`frontend/datos/`. Diseño en [`specs/001-backend-api-bbdd/`](../specs/001-backend-api-bbdd/).

Todo corre en el PC del propietario: API y PostgreSQL en Docker Compose; el scraper, fuera de
Docker, como tarea programada de Windows; un Cloudflare Tunnel publica solo las rutas de lectura.

## Arranque local (un solo comando)

```bash
cd backend
cp .env.example .env        # y edita INGEST_SECRET / POSTGRES_PASSWORD
docker compose up --build
```

La API queda en `http://127.0.0.1:8000` (solo accesible desde el propio equipo; usa `127.0.0.1` y no `localhost`, que en Windows añade ~2 s por petición al probar IPv6 primero). Las migraciones
de Alembic corren solas al arrancar el contenedor `api`. Tras el primer arranque, carga los datos
actuales una sola vez:

```bash
docker compose exec api python -m scripts.migrar_datos_existentes
```

El contenedor `api` monta `../frontend` en solo lectura para esa migración.

`frontend/datos/` se retiró del repositorio (spec 001, T052) tras migrar y verificar los datos.
Si alguna vez hay que volver a migrar sobre una base vacía, recupera los JSON de la etiqueta
`pre-retirada-fase1`: `git checkout pre-retirada-fase1 -- frontend/datos`, ejecuta la migración y
borra la carpeta de nuevo (`git rm -r --cached frontend/datos` si no quieres commitearla).

## Variables de entorno

| Variable | Uso | Por defecto |
|---|---|---|
| `DATABASE_URL` | Conexión de SQLAlchemy | `sqlite:///./housescore.db` (en compose: el contenedor `db`) |
| `INGEST_SECRET` | Secreto Bearer de `POST /ingest`. Sin él, la ingesta rechaza todo | — (obligatorio en compose) |
| `RATE_LIMIT` | Límite por IP de los endpoints de lectura | `60/minute` |
| `POSTGRES_PASSWORD` | Contraseña de la base de datos en compose | `housescore` |
| `HOUSESCORE_API_URL` | URL de la API para el cliente del scraper y el dashboard | `http://127.0.0.1:8000` |
| `TEST_DATABASE_URL` | Base de datos de los tests | `sqlite://` (memoria) |

`backend/.env` no se versiona.

## Endpoints

| Ruta | Acceso |
|---|---|
| `GET /listings` (`municipio`, `incluir_retirados`) | público, con rate limiting por IP |
| `GET /historico` (`desde`, `hasta`) | público, con rate limiting por IP |
| `POST /ingest` | solo `localhost` + `Authorization: Bearer <INGEST_SECRET>`; el túnel no lo publica |

## Tests

```bash
# En el host (SQLite en memoria, sin tocar datos reales)
python -m venv .venv && .venv/Scripts/pip install -e ".[dev]"
.venv/Scripts/python -m pytest

# Contra PostgreSQL efímero (no usa el volumen de datos reales)
docker compose --profile test run --rm test
```

`tests/integration/test_entorno_local.py` solo se ejecuta si defines `HOUSESCORE_E2E_URL`.

## Sin Docker (desarrollo)

```bash
cd backend
python -m venv .venv && .venv/Scripts/pip install -e ".[dev]"
export DATABASE_URL=sqlite:///./housescore.db INGEST_SECRET=dev
.venv/Scripts/python -m alembic upgrade head
.venv/Scripts/python -m scripts.migrar_datos_existentes   # una sola vez, sobre base vacía
.venv/Scripts/python -m uvicorn app.main:app --reload
```

## Enviar una pasada del scraper

```bash
INGEST_SECRET=... python -m worker.scraper.client ruta/al/last_property_data.json
```

Desde el scorer: `from worker.scraper.client import enviar_pasada`. La ingesta es idempotente
por `url`, así que reintentar es seguro. `worker/scraper/run_scraper.ps1` envuelve la ejecución
con log en `backend/logs/`.

## El scorer (`worker/scraper/`)

Copia adaptada de los scripts de `~/AppData/Local/hermes/scripts/`: `property_scorer_common.py`,
los lotes `property_scorer_madrid.py`, `property_scorer_toledo.py` y `property_scorer_idealista.py`,
y el orquestador `property_scorer_all.py`. Cambios respecto a los originales, y nada más:

1. Al empezar, cada lote llama a `verificar_api()` (falla pronto si la API está caída).
2. El historial (`first_seen`, último precio) sale de `GET /listings?incluir_retirados=true` en vez de
   `frontend/datos/*.json`. Las puntuaciones dependen de él (bajadas de precio y días en el mercado).
3. Al terminar, `publicar_pasada()` envía el lote a `POST /ingest` en vez de escribir el snapshot
   diario y hacer `git commit` + `push`. Si falla, el lote se guarda en `HERMES_DATA_DIR/pendientes/`
   y se reenvía con `python -m worker.scraper.client <fichero>`.

Los originales de `~/AppData/Local/hermes/scripts/` **no se han tocado**. El job de hermes
(`Buscador Pisos`, `0 9 * * *`) ya no los usa: su `script` es `housescore_scraper.py`, una copia de
`ops/hermes_launcher.py`. Hace falta un lanzador porque hermes ejecuta sus scripts con su propio
Python 3.14, en el que Playwright no importa (`greenlet._greenlet`), y solo admite scripts dentro de
`~/AppData/Local/hermes/scripts/`. El lanzador (solo librería estándar) comprueba que la API responde,
carga `INGEST_SECRET` de `backend/.env` y ejecuta `worker/scraper/property_scorer_all.py` con el
Python del entorno de hermes (que tiene `playwright`, `playwright_stealth` y `httpx`).

Si cambias `ops/hermes_launcher.py`, vuelve a copiarlo:
`cp backend/ops/hermes_launcher.py ~/AppData/Local/hermes/scripts/housescore_scraper.py`.
La sesión de idealista (`idealista_session.json`) sigue fuera del repo, en `HERMES_DATA_DIR`.
Idealista bloquea hoy todos los municipios (es esperado y no rompe el job). El scorer sigue leyendo y
escribiendo `frontend/config/precios_referencia.json`, que ya no se commitea.

## Dashboard (Streamlit)

El dashboard lee de esta API (no de `frontend/datos/`). Con el backend en marcha:

```bash
pip install -r frontend/requirements.txt
streamlit run frontend/dashboard/app.py
```

Consulta `http://127.0.0.1:8000`; para otra dirección, `HOUSESCORE_API_URL=... streamlit run ...`.
Si la API no responde, muestra un aviso con la dirección consultada y ninguna cifra.

## Estructura

```text
app/        API (main, api/, models/, services/, db/, core/, schemas.py)
worker/     cliente del scraper (client.py) y run_scraper.ps1
alembic/    migraciones
scripts/    migrar_datos_existentes.py
ops/        túnel, backups y tareas programadas
tests/      unit/, contract/, integration/
```
