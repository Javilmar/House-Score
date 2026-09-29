# Investigación (Fase 0): Backend (API + Base de Datos) para HouseScore

## 1. Framework de la API

**Decisión**: FastAPI (Python) sobre Uvicorn.

**Motivo**: reutiliza directamente el lenguaje del motor de scoring
existente (Principio I — nada que portar ni envolver); validación de datos
declarativa vía Pydantic, que encaja bien con las entidades ya definidas en
el spec; documentación OpenAPI autogenerada, útil como contrato vivo para
`contracts/api.md`; ecosistema maduro de testing (`httpx`/`TestClient`) que
encaja con el mandato de TDD (Principio IV).

**Alternativas consideradas**:
- *Flask*: requeriría añadir manualmente validación y generación de
  esquema; sin ventaja real para este alcance.
- *Django REST Framework*: mucho más peso (ORM propio, admin, auth
  batteries-included) del que necesita un backend de un único cliente.

## 2. Base de datos y acceso a datos

**Decisión**: PostgreSQL 16 + SQLAlchemy 2.x + Alembic para migraciones.

**Motivo**: imagen oficial `postgres:16` en Docker Compose, con volumen
persistente en el PC del propietario; adecuada para este volumen (≈500
listings + histórico diario) y portable: si algún día la API se muda a un
hosting, la base de datos no cambia. Alembic da migraciones versionadas y
reproducibles, necesarias tanto para el entorno local (Historia 3 / SC-003)
como para evolucionar el esquema.

**Alternativas consideradas**:
- *SQLite*: bastaría con un solo escritor local y sería más simple de
  arrancar, pero se descarta para no reescribir el acceso a datos si la API
  se despliega después en un hosting con Postgres; la diferencia de coste
  en local es pequeña.
- *MongoDB*: los datos son claramente relacionales (listing → historial de
  precio, listing → municipio → precio de referencia); un esquema
  relacional expresa mejor esas relaciones e integridad que un modelo
  documental.

## 3. Rate limiting de los endpoints públicos (FR-012)

**Decisión**: `slowapi` (middleware de rate limiting para Starlette/FastAPI,
basado en `limits`), aplicado por IP a los endpoints `GET /listings` y
`GET /historico`.

**Motivo**: es una librería Python nativa de FastAPI, sin necesidad de
infraestructura adicional (no requiere Redis para este volumen de tráfico —
un límite en memoria por proceso es suficiente para una única instancia de
la API); mínima superficie de configuración. Detrás del túnel, la IP de
origen llega en la cabecera `CF-Connecting-IP`; el limitador debe leerla, o
todas las peticiones parecerían venir de una misma IP.

**Alternativas consideradas**:
- *Rate limiting en Cloudflare*: existe en su plataforma, pero añade una
  dependencia de configuración externa; se puede sumar más adelante.
- *Middleware propio*: reinventar una rueda ya resuelta por `slowapi` sin
  beneficio adicional.

## 4. Aislamiento del endpoint de ingesta (FR-010/FR-011)

**Contexto**: la API corre en el PC del propietario y se publica a internet
con un Cloudflare Tunnel para que el front desplegado en la nube pueda leer.
Un túnel enruta lo que se configure, así que el aislamiento se decide ahí.

**Decisión** (dos capas):
1. **Sin ruta pública.** La configuración del túnel (`cloudflared`, reglas
   de `ingress` por ruta) solo publica `GET /listings` y `GET /historico`;
   cualquier otra ruta, incluida `POST /ingest`, cae en la regla final
   `http_status:404`. El scraper, en el mismo equipo, llama a
   `http://localhost:8000/ingest`.
2. **Secreto compartido** como defensa en profundidad: `POST /ingest` exige
   `Authorization: Bearer <INGEST_SECRET>` (variable de entorno, fuera del
   repo). Cubre un error de configuración del túnel o un futuro cambio de
   despliegue.

Es una solución deliberadamente mínima: no es un sistema de usuarios ni de
permisos. No cambia la decisión de `/speckit-clarify` sobre los endpoints de
*lectura* (públicos, sin auth, con rate limiting, FR-012).

**Alternativas consideradas**:
- *Solo secreto compartido, endpoint publicado*: descartado; si se filtra el
  secreto, cualquiera podría escribir. Mejor no exponer la ruta.
- *Tailscale en vez de Cloudflare Tunnel*: la API sería privada, pero un
  front desplegado en la nube no podría leerla. Válido si el front también
  corre en el equipo.
- *Que el scraper escriba directamente a PostgreSQL, sin pasar por la API*:
  ya descartado explícitamente en `/speckit-clarify` (Q1: A — endpoint de
  escritura en la API), porque las reglas de negocio viven en la API.

**Nota a futuro (confirmada con el propietario, 2026-09-08)**: el secreto
compartido es una solución deliberadamente mínima para esta primera versión,
en la que el único "cliente" que escribe es el propio scraper.
El propietario ha confirmado que en el futuro quiere que HouseScore tenga
usuarios reales. Cuando eso ocurra, esta autenticación de token único DEJA
DE SER SUFICIENTE y NO debe extenderse ad hoc (p. ej. añadiendo más tokens
fijos) — hará falta un spec propio de autenticación/autorización de
usuarios (sesiones u OAuth, gestión de credenciales, roles/permisos si
aplica) que sustituya este mecanismo por completo, no que lo parchee.

## 5. Migración del scraper al repositorio y dónde se ejecuta

**Hallazgo 1**: el scorer no vive en este repositorio: está en el ordenador
del propietario, en `~/AppData/Local/hermes/scripts/`, fuera de control de
versiones (`frontend/dashboard/app.py` solo lo referencia). Son cinco ficheros: `property_scorer_common.py`, los tres lotes (`property_scorer_madrid.py`, `property_scorer_toledo.py`, `property_scorer_idealista.py`) y el orquestador `property_scorer_all.py`; los lotes y el común se modificaron por última vez el 2026-09-27, tras redactarse la primera versión de esta spec. El cron de hermes (`0 9 * * *`) ejecuta `property_scorer_all.py`.

**Hallazgo 1b**: cada lote termina escribiendo `frontend/datos/YYYY-MM-DD.json` (con merge de los otros lotes del día) y haciendo `git commit` + `pull --rebase` + `push`. Además **lee** esos JSON (`load_history`) para calcular `first_seen`, `price_drop` y `previous_price`, y `score_property` los usa. Por tanto no basta con cambiar el envío: el historial también debe venir de la API.

**Hallazgo 2**: el scraper usa Playwright con Chromium (`playwright_stealth`)
y, para idealista, carga cookies de una sesión capturada a mano con
`capture_idealista_session.py` (Chromium visible, el usuario resuelve el
CAPTCHA). Desde una IP de datacenter idealista probablemente bloquearía o
pediría CAPTCHA, y las cookies caducan. Por eso la propuesta anterior de un
Background Worker en la nube se descarta.

**Decisión**: los cinco ficheros del scorer se copian a `backend/worker/scraper/` (los originales de hermes no se tocan hasta el cambio de cron). En las copias, cada lote (a) comprueba la API al empezar (`verificar_api`), para no scrapear con la API caída; (b) obtiene el historial de `GET /listings?incluir_retirados=true` (`cargar_historial_api`) en vez de `frontend/datos`; y (c) envía su pasada con `publicar_pasada` en lugar de escribir el snapshot y hacer `git push`. Si el envío falla, el lote se guarda en `pendientes/` (dentro de `HERMES_DATA_DIR`) y se puede reenviar con `python -m worker.scraper.client`. El scraper sigue ejecutándose **en el host de Windows**, no en Docker, lanzado por el cron de hermes o por una tarea programada de Windows. El script de captura de sesión y el fichero de cookies siguen siendo locales y **no se versionan** (contienen datos de sesión).

**Alternativas consideradas**:
- *Worker en un hosting en la nube*: descartado por lo anterior.
- *Worker en la nube solo para pisos.com*: viable, pero duplica el
  despliegue por una sola fuente; se puede reconsiderar más adelante.

## 6. Entorno de ejecución y entorno de pruebas (Historia 3 / SC-003)

**Decisión**: `docker-compose.yml` con dos servicios: `api` (build del
`Dockerfile` de `backend/`) y `db` (imagen oficial `postgres:16` con volumen
persistente), ambos con `restart: unless-stopped`. Docker Desktop se
configura para arrancar con Windows, de modo que tras un reinicio todo
vuelve solo (FR-015). Un único `docker compose up` deja ambos operativos;
Alembic corre las migraciones automáticamente al arrancar `api`
(`entrypoint.sh`).

**Pruebas**: como la base de datos local pasa a contener los datos reales,
la suite de tests NO debe usarla. `docker compose run --rm api pytest`
levanta una base de datos de pruebas aparte (servicio o perfil `test`,
efímero, sin volumen) para no tocar datos reales (Historia 3, escenario 2).

**Copias de seguridad (FR-016)**: `pg_dump` periódico (tarea programada) a
una ubicación fuera del disco que aloja el volumen (otro disco o
sincronizado a la nube), conservando varias copias con rotación. Se prueba
la restauración en un entorno limpio (SC-007).

**Arranque de `cloudflared`**: instalado como servicio de Windows con la
configuración de rutas de la sección 4.

**Motivo**: cumple SC-003 y SC-006 (arranque sin pasos manuales) y aísla las
pruebas de los datos reales.

**Alternativas consideradas**: pedir a quien desarrolla que instale
PostgreSQL nativamente — se descarta explícitamente por el spec
(Historia 3: "sin tener que instalar ni configurar manualmente una base de
datos").

---

Todos los `NEEDS CLARIFICATION` del Contexto Técnico quedan resueltos con
las decisiones anteriores.
