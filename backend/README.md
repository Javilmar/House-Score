# Backend de HouseScore

API (FastAPI) + base de datos (PostgreSQL) que sustituyen el flujo de JSON commiteados en
`frontend/datos/`. Diseño en [`specs/001-backend-api-bbdd/`](../specs/001-backend-api-bbdd/).

En producción la API corre en Render (Docker, raíz `backend`) sobre Neon (PostgreSQL) y la lee el
front estático de `frontend/web`. En local, API y PostgreSQL van en Docker Compose; el scraper, fuera
de Docker, lo lanza el cron `Buscador Pisos` de hermes en el PC del propietario.

## Arranque local (un solo comando)

```bash
cd backend
cp .env.example .env        # y edita INGEST_SECRET / POSTGRES_PASSWORD
docker compose up --build
```

La API queda en `http://127.0.0.1:8000` (solo accesible desde el propio equipo; usa `127.0.0.1` y no `localhost`, que en Windows añade ~2 s por petición al probar IPv6 primero). Las migraciones
de Alembic corren solas al arrancar el contenedor `api`.

## Variables de entorno

| Variable | Uso | Por defecto |
|---|---|---|
| `DATABASE_URL` | Conexión de SQLAlchemy. **Obligatoria**: sin ella la API no arranca | — (en compose: el contenedor `db`; en Render: Neon con pooler) |
| `INGEST_SECRET` | Secreto Bearer de `POST /ingest`. Sin él, la ingesta rechaza todo | — (obligatorio en compose) |
| `RATE_LIMIT` | Límite por IP de los endpoints de lectura | `60/minute` |
| `CORS_ORIGINS` | Orígenes (separados por comas) del front que pueden leer la API desde el navegador; solo `GET` | vacío (ninguno) |
| `POSTGRES_PASSWORD` | Contraseña de la base de datos en compose | `housescore` |
| `HOUSESCORE_API_URL` | URL de la API para el cliente del scraper (en producción, la API de Render) | `http://127.0.0.1:8000` |
| `TEST_DATABASE_URL` | Base de datos de los tests | `sqlite://` (memoria) |

`backend/.env` no se versiona.

## Endpoints

| Ruta | Acceso |
|---|---|
| `GET /listings` (`municipio`, `incluir_retirados`) | público, con rate limiting por IP |
| `GET /historico` (`desde`, `hasta`) | público, con rate limiting por IP |
| `POST /ingest` | `Authorization: Bearer <INGEST_SECRET>` (sin el secreto, rechaza todo) |

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
.venv/Scripts/python -m uvicorn app.main:app --reload
```

## Enviar una pasada del scraper

```bash
INGEST_SECRET=... python -m worker.scraper.client <pendiente>.json \
    --api-url https://house-score.onrender.com
```

Sin `--api-url` usa `HOUSESCORE_API_URL` (o `http://127.0.0.1:8000`). `INGEST_SECRET` debe ser el mismo
que tiene la API de Render.

Desde el scorer: `from worker.scraper.client import enviar_pasada`. La ingesta es idempotente
por `url`, así que reintentar es seguro. `worker/scraper/run_scraper.ps1` envuelve la ejecución
con log en `backend/logs/`.

## El scorer (`worker/scraper/`)

Copia adaptada de los scripts de `~/AppData/Local/hermes/scripts/`: `property_scorer_common.py`,
un lote por zona `property_scorer_lote.py <zona>` y el orquestador `property_scorer_all.py`, que
ejecuta un lote por cada zona de `ZONAS` (`property_scorer_common.py`):

| Zona | Tope | fotocasa | Fichas por pasada |
|---|---|---|---|
| `madrid_sur` (18 municipios) | 300.000 € | sí | 30 |
| `madrid_este` (6) | 350.000 € | sí | 15 |
| `madrid_sureste` (5) | 300.000 € | sí | 15 |
| `madrid_norte` (6) | 400.000 € | sí | 15 |
| `toledo_norte` (5) | 300.000 € | no | 15 |

Cambios respecto a los originales:

1. Al empezar, cada lote llama a `verificar_api()` (falla pronto si la API está caída).
2. El historial (`first_seen`, último precio) sale de `GET /listings?incluir_retirados=true` en vez de
   `frontend/datos/*.json`. Las puntuaciones dependen de él (bajadas de precio y días en el mercado).
   También trae el `detalle` guardado: si un anuncio ya tiene ficha leída (`ficha_detalle`), se
   reutiliza (`reutilizar_ficha`) y la lectura de fichas de la pasada (tabla de arriba) se dedica a
   los mejores anuncios que aún no la tienen.
3. Cada pasada envía **todo** lo scrapeado (ya no hay filtro de «vistos»): así `ultima_aparicion`
   avanza, no se retiran anuncios vivos y se detectan las bajadas de precio.
4. Sin exterior detectado se resta 25 solo si la ficha está leída; sin ficha, «❔ Exterior sin
   verificar (0)».
5. Los anuncios «sin posesión», okupados, de nuda propiedad o subastas (`es_problematico`) no se
   envían a la API, ni los que la ficha revela por encima del tope de su zona (`supera_tope`: el
   precio del listado a veces es menor que el real). Sus urls se apuntan en
   `HERMES_DATA_DIR/descartados.json` (caducan a los 180 días) para no volver a leer su ficha en
   cada pasada.
6. Al terminar, `publicar_pasada()` envía el lote a `POST /ingest` en vez de escribir el snapshot
   diario y hacer `git commit` + `push`. Si falla, el lote se guarda en `HERMES_DATA_DIR/pendientes/`
   y se reenvía con `python -m worker.scraper.client <fichero> --api-url https://house-score.onrender.com`
   (con `INGEST_SECRET` definido).

**Contra la API de producción:** `HOUSESCORE_API_URL` debe apuntar a la API de Render
(`https://house-score.onrender.com`) y `INGEST_SECRET` coincidir con el de Render. El lanzador de hermes
lee `HOUSESCORE_API_URL` y `HOUSESCORE_PYTHON` de las variables de entorno (de usuario en Windows; hermes
debe reiniciarse tras cambiarlas) e `INGEST_SECRET` de `backend/.env`. Con el valor por defecto
(`http://127.0.0.1:8000`) las pasadas irían a la API local, no a la que lee el front. Como Render duerme
la API sin uso, el lanzador espera hasta 180 s a que responda.

Montaje actual (2026-10-22): `HOUSESCORE_PYTHON` = `%LOCALAPPDATA%\housescore\venv\Scripts\python.exe`
(venv con `playwright`, `playwright-stealth`, `httpx` y Chromium de Playwright) y un enlace
`%USERPROFILE%\house-dashboard` → este repo, que es la ruta que esperan el lanzador y el scorer.

Los originales de `~/AppData/Local/hermes/scripts/` **no se han tocado**. El job de hermes
(`Buscador Pisos`, `0 9 * * *`) ya no los usa: su `script` es `housescore_scraper.py`, una copia de
`ops/hermes_launcher.py`. Hace falta un lanzador porque hermes ejecuta sus scripts con su propio
Python 3.14, en el que Playwright no importa (`greenlet._greenlet`), y solo admite scripts dentro de
`~/AppData/Local/hermes/scripts/`. El lanzador (solo librería estándar) comprueba que la API responde,
carga `INGEST_SECRET` de `backend/.env` y ejecuta `worker/scraper/property_scorer_all.py` con el
Python del entorno de hermes (que tiene `playwright`, `playwright_stealth` y `httpx`).

Si cambias `ops/hermes_launcher.py`, vuelve a copiarlo:
`cp backend/ops/hermes_launcher.py ~/AppData/Local/hermes/scripts/housescore_scraper.py`.

**Pasada de recuperación.** hermes solo dispara el job si el PC está encendido a las 09:00. Por eso
`ops/registrar_tareas.ps1` registra también la tarea `HouseScore-Scraper` (10:00, `StartWhenAvailable`,
requiere `HOUSESCORE_PYTHON`), que lanza el mismo `hermes_launcher.py`. Al terminar con código 0 el
lanzador escribe la fecha de hoy en `HERMES_DATA_DIR/ultima_pasada_ok.txt` (por defecto
`~/AppData/Local/hermes/ultima_pasada_ok.txt`); si ya contiene la fecha de hoy, el siguiente disparo
dice «Ya hay una pasada completa de hoy» y no repite. Una pasada fallida no escribe la marca, así que
se reintenta sola (la ingesta es idempotente por `url`).

## Front web

El front es estático y vive en [`../frontend/web`](../frontend/web) (React + Vite). Lee `GET /listings` y
`GET /historico` de esta API; con el backend en marcha: `cd ../frontend/web && npm ci && npm run dev`
(`VITE_API_URL` para otra API). Ver [`../README.md`](../README.md) y
[`../frontend/web/FUNCIONALIDADES.md`](../frontend/web/FUNCIONALIDADES.md). La API debe incluir el origen
del front en `CORS_ORIGINS`.

## Copia de seguridad (Neon)

`ops/backup.ps1` vuelca la base de Neon con `pg_dump -Fc` ejecutado en un contenedor
`postgres:18-alpine` (hace falta Docker, no un cliente de PostgreSQL) y rota los volcados:

```powershell
.\ops\backup.ps1 -Destino "$env:OneDrive\backups\housescore" -Conservar 14
```

Lee `DATABASE_URL_UNPOOLED` (conexión directa; el pooler no sirve para `pg_dump`) o, si no existe,
`DATABASE_URL`, del entorno o de `.env.local` en la raíz del repo. Restaurar en una base vacía:

```bash
docker run --rm -v "<carpeta>:/b" postgres:18-alpine pg_restore -d "<url-destino>" --no-owner /b/<volcado>.dump
```

## Estructura

```text
app/        API (main, api/, models/, services/, db/, core/, schemas.py)
worker/     cliente del scraper (client.py) y run_scraper.ps1
alembic/    migraciones
ops/        lanzador de hermes, backups y tareas programadas
tests/      unit/, contract/, integration/
```
