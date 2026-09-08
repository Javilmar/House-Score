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

**Motivo**: Render ofrece PostgreSQL gestionado con un tier gratuito/barato
adecuado para este volumen (≈500 listings + histórico diario); soporta
bien accesos concurrentes API+worker (a diferencia de SQLite); Alembic da
migraciones versionadas y reproducibles, necesarias tanto para el entorno
local (Historia 3 / SC-003) como para evolucionar el esquema sin downtime.

**Alternativas consideradas**:
- *SQLite*: más simple de arrancar, pero Render no garantiza disco
  persistente entre despliegues de un Web Service/Worker, y no resuelve
  bien la escritura concurrente worker+API; se descarta.
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
un límite en memoria por proceso es suficiente para un servicio de un
único Web Service en Render); mínima superficie de configuración.

**Alternativas consideradas**:
- *Rate limiting a nivel de plataforma (Render)*: no disponible en los
  planes de entrada de Render; se descarta por coste.
- *Middleware propio*: reinventar una rueda ya resuelta por `slowapi` sin
  beneficio adicional.

## 4. Aislamiento del endpoint de ingesta (FR-010/FR-011) — hallazgo importante

**Hallazgo**: en Render, un *Web Service* siempre recibe una URL pública
HTTPS; el aislamiento real de red entre servicios del mismo proyecto
(*Private Services*, sin URL pública en absoluto) es una función del plan
**Team** (de pago), no está disponible en los planes Free/Starter/Individual.
Esto significa que la premisa original de FR-011 ("no requiere autenticación
porque no existe ninguna ruta pública") no es literalmente alcanzable sin
asumir ese coste adicional.

**Decisión**: mantener el endpoint de ingesta (`POST /ingest`) dentro del
mismo Web Service que la API pública, pero protegido por un **secreto
compartido simple** (un token fijo en una variable de entorno de Render,
enviado por el worker en una cabecera `Authorization: Bearer <token>`). No
es un sistema de usuarios ni de permisos — es una única constante
compartida entre el worker y la API, equivalente en espíritu a "nadie de
fuera puede escribir", pero factible en el plan gratuito/barato de Render.

**Impacto en el spec**: FR-011 se mantiene en intención (el endpoint de
escritura no es de uso público) pero su mecanismo pasa de "aislamiento de
red" a "aislamiento de red disponible cuando el hosting lo permita + secreto
compartido como defensa adicional siempre". No cambia ninguna decisión ya
tomada en `/speckit-clarify` sobre autenticación de los endpoints de
*lectura* (siguen públicos y sin auth, FR-012).

**Alternativas consideradas**:
- *Pagar el plan Team de Render para tener un Private Service real*:
  descartado por coste para un proyecto personal; se puede reconsiderar
  más adelante si el proyecto lo justifica.
- *Que el worker escriba directamente a PostgreSQL, sin pasar por la API*:
  ya descartado explícitamente en `/speckit-clarify` (Q1: A — endpoint de
  escritura en la API).

**Nota a futuro (confirmada con el propietario, 2026-09-08)**: el secreto
compartido es una solución deliberadamente mínima para esta primera versión,
en la que el único "cliente" que escribe es el propio worker del scraper.
El propietario ha confirmado que en el futuro quiere que HouseScore tenga
usuarios reales. Cuando eso ocurra, esta autenticación de token único DEJA
DE SER SUFICIENTE y NO debe extenderse ad hoc (p. ej. añadiendo más tokens
fijos) — hará falta un spec propio de autenticación/autorización de
usuarios (sesiones u OAuth, gestión de credenciales, roles/permisos si
aplica) que sustituya este mecanismo por completo, no que lo parchee.

## 5. Migración del scraper (`property_scorer.py`) al repositorio

**Hallazgo**: el script que scrapea y puntúa (`property_scorer.py`) no vive
en este repositorio — corre en el ordenador del propietario, en
`~/AppData/Local/hermes/scripts/property_scorer.py` (referenciado desde
`frontend/dashboard/app.py`, pero fuera de control de versiones).

**Decisión**: como parte de la implementación (no de este plan en sí, pero
como prerrequisito que `/speckit-tasks` debe reflejar como tarea explícita),
ese script se trae a `backend/worker/scraper/` y se le añade el cliente que
llama a `POST /ingest` en lugar de escribir JSON local + hacer `git push`
vía `guardar.py`.

**Alternativas consideradas**: dejar `property_scorer.py` donde está y que
solo un script "puente" corra en Render llamando a un `property_scorer.py`
remoto — no tiene sentido: el propósito explícito de este backend es que el
scraper deje de depender del ordenador del propietario (Historia 2).

## 6. Entorno local reproducible (Historia 3 / SC-003)

**Decisión**: `docker-compose.yml` con tres servicios: `api` (build del
`Dockerfile` de `backend/`), `db` (imagen oficial `postgres:16`), y
`worker` (mismo build que `api`, distinto comando de arranque). Un único
`docker compose up` deja los tres operativos; Alembic corre las migraciones
automáticamente al arrancar `api` (o como paso previo en un script
`entrypoint.sh`).

**Motivo**: cumple SC-003 (arranque con un único comando, sin pasos
manuales) y aísla las pruebas de cualquier dato de producción, ya que la
base de datos del `docker-compose` es efímera y local.

**Alternativas consideradas**: pedir a quien desarrolla que instale
PostgreSQL nativamente — se descarta explícitamente por el spec
(Historia 3: "sin tener que instalar ni configurar manualmente una base de
datos").

---

Todos los `NEEDS CLARIFICATION` del Contexto Técnico quedan resueltos con
las decisiones anteriores.
