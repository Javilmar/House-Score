---
spec: spec-007
slug: backend-api-personalizacion
title: "Backend API + BD para perfiles de usuario y migracion de listings"
status: draft
effort: large
summary: "Construir una API (FastAPI + SQLModel + PostgreSQL) autohospedada en una VPS, que sustituye el flujo actual de listings en JSON+git por almacenamiento en base de datos, añade autenticación y perfiles de usuario (grupo cerrado inicialmente), y aloja también el scraper y el dashboard Streamlit en la misma VPS detrás de Nginx."
created: 2026-09-07
---

## Summary

Hoy la app es 100% estática desde el punto de vista de infraestructura: un
scraper local guarda pasadas diarias como JSON en `datos/`, `guardar.py` hace
`git commit`+`push`, y Streamlit Community Cloud sirve `app.py` leyendo esos
JSON directamente del repo. No hay usuarios, ni sesiones, ni personalización:
cualquiera que abra la URL ve exactamente los mismos datos y filtros
volátiles (se resetean al recargar).

Este spec cubre la primera pieza de una evolución más amplia hacia una app
"con usuarios" (perfiles, favoritos, alertas guardadas — fuera de alcance
aquí, ver Non-Goals): construir el backend que lo hará posible. Esto implica
un cambio de arquitectura de infraestructura completo: de "repo de git como
base de datos + hosting gratuito sin estado" a "servidor propio con base de
datos relacional, corriendo 24/7, con autenticación real".

Se decidió autohospedar todo (scraper + API + BD + Streamlit) en una VPS
propia con Docker, Nginx como reverse proxy y Let's Encrypt vía Certbot,
usando un dominio que el operador ya posee.

## Goals

1. Nueva API en FastAPI (Python) que expone listings, autenticación de
   usuarios y perfiles — sustituye a `datos/*.json` como fuente de verdad de
   los listings.
2. Modelos de datos vía **SQLModel** (Pydantic + SQLAlchemy) con migraciones
   gestionadas por **Alembic**, sobre **PostgreSQL**.
3. Sistema de autenticación con soporte de **grupo cerrado por invitación**
   en v1 (solo el operador + un grupo reducido que él invita manualmente) —
   diseñado de forma que no bloquee abrir registro público más adelante
   (fuera de alcance de v1, ver Non-Goals).
4. Migración one-time del histórico completo de `datos/*.json` (todas las
   pasadas diarias existentes) a PostgreSQL, preservando la serie temporal
   necesaria para los gráficos de Tab 3 (Evolución y análisis).
5. El scraper que hoy corre en local se traslada a la VPS, ejecutándose por
   cron, y escribe directamente en la base de datos (ya no genera JSON ni
   hace `git push`).
6. El dashboard Streamlit se traslada también a la VPS (deja de vivir en
   Streamlit Community Cloud) y pasa a leer de la API/BD en vez de los JSON
   locales del repo.
7. Infraestructura en VPS: Docker + docker-compose (API, BD, Streamlit como
   contenedores separados), Nginx como reverse proxy con Certbot para
   HTTPS, usando subdominios del dominio ya propiedad del operador
   (p.ej. `app.dominio.com`, `api.dominio.com`).
8. Higiene operativa mínima de la VPS: firewall (ufw), acceso SSH solo por
   clave, actualizaciones de seguridad automáticas, backups periódicos de
   la BD, y monitorización de uptime (aviso si el servicio cae).

## Non-Goals

- **Registro público abierto** no es parte de v1 — el sistema de auth debe
  ser extensible a ello (no un hack de usuarios hardcodeados), pero
  verificación de email, recuperación de contraseña self-service para
  desconocidos, protección anti-spam/bots, etc. se diseñan en un spec
  posterior cuando se decida abrir el registro.
- **Favoritos, alertas guardadas, preferencias de usuario** y cualquier
  funcionalidad de personalización visible en el dashboard quedan fuera de
  este spec — este spec entrega solo la infraestructura (API+BD+auth
  básica) sobre la que se construirán después.
- **Elección de proveedor de VPS concreto** (Hetzner/DigitalOcean/OVH/etc.)
  se decide en `/ai-plan`, no bloquea este spec.
- **Mitigación de bloqueo anti-bot por IP de datacenter** (el scraper
  saliendo desde la VPS en vez de una IP residencial) se documenta como
  riesgo (ver Risks) pero su solución técnica (proxies residenciales,
  rotación de IP, etc., si hiciera falta) es un spec aparte si el problema
  se materializa — no se sobre-diseña de antemano.
- **Caddy** como alternativa de reverse proxy se descartó explícitamente a
  favor de Nginx (decisión del operador, ver Decisions) — no se reabre aquí.
- No se rediseña el sistema de scoring (`property_scorer.py`) ni las
  reglas de negocio de filtrado de zona — se migran tal cual a la nueva
  capa de datos.

## Decisions

| # | Decisión | Alternativa descartada | Razón |
|---|----------|------------------------|-------|
| D-007-01 | La API sustituye por completo el flujo JSON-en-git como fuente de listings (no coexisten ambos sistemas en paralelo indefinidamente). | Mantener JSON-en-git para listings y usar la API solo para usuarios/perfiles. | El operador priorizó unificar todo en un solo sistema desde el principio en vez de mantener dos fuentes de verdad de datos de listings. |
| D-007-02 | Backend en Python + FastAPI. | Otro lenguaje/framework. | Coherencia con el stack existente (Streamlit, scraper, scoring ya en Python) — permite reusar `property_scorer.py` como librería sin duplicar lógica ni mantener dos stacks. |
| D-007-03 | ORM: SQLModel + Alembic para migraciones. | SQLAlchemy "puro" (+Alembic); SQL a pelo. | SQLModel evita duplicar la definición de modelos (API request/response vs tabla de BD) al combinar Pydantic+SQLAlchemy; menos boilerplate para el volumen de complejidad esperado. |
| D-007-04 | Motor de base de datos: PostgreSQL. | SQLite. | Necesario para concurrencia real de múltiples usuarios (aunque v1 sea grupo cerrado, se diseña pensando en crecer), y es el estándar de facto para self-hosted con Docker + SQLModel/Alembic. |
| D-007-05 | Infraestructura autohospedada en una VPS propia (Docker), en vez de un PaaS gestionado (Railway/Render/Fly.io) o serverless (Vercel). | PaaS gestionado; Vercel. | El operador prioriza control total sobre la infraestructura y evitar cuotas de servicio gestionado recurrentes, aceptando explícitamente cargar con el mantenimiento operativo (parches, backups, monitorización) a cambio. Vercel se descartó por no encajar con Streamlit (proceso persistente con estado) ni con ejecuciones de scraper más largas que el límite de funciones serverless. |
| D-007-06 | Grupo cerrado por invitación en v1 (no registro público), pero el modelo de auth se diseña extensible a registro público futuro. | Registro público abierto desde v1. | El operador confirmó que la intención a futuro es abrir el registro, pero explícitamente no en v1 — evita sobre-construir verificación de email/anti-spam/recuperación de contraseña self-service antes de que haga falta. |
| D-007-07 | El dashboard Streamlit se traslada a la misma VPS (deja Streamlit Community Cloud). | Streamlit se queda en Streamlit Community Cloud llamando a la API por HTTPS como cliente externo. | El operador prefirió consolidar todo el stack en un solo lugar bajo su control, aceptando perder el hosting gratuito de Streamlit Cloud a cambio. |
| D-007-08 | Reverse proxy: Nginx + Certbot. | Caddy (HTTPS automático, configuración más simple). | Decisión explícita del operador tras conocer el trade-off (Nginx es más manual pero más estándar/extendido); se documenta para que quede claro que Certbot y su renovación de certificados quedan a cargo del operador, no automatizados como en Caddy. |
| D-007-09 | El scraper se traslada a ejecutarse en la VPS (cron), escribiendo directamente en la BD. | El scraper se queda en el ordenador local del operador y hace `POST` HTTPS a la API en vez de `git push`. | El operador priorizó independencia de que su ordenador esté encendido sobre el riesgo de bloqueo anti-bot por IP de datacenter (riesgo aceptado conscientemente, ver Risks). |
| D-007-10 | Se migra el histórico completo de `datos/*.json` a PostgreSQL en un script one-time. | Empezar la BD en limpio y perder el histórico de meses en los gráficos de evolución (Tab 3). | El operador quiere conservar la continuidad de los gráficos de tendencias existentes; no tiene sentido perder meses de datos ya recolectados. |
| D-007-11 | El dominio ya propiedad del operador se reutiliza vía subdominios (`app.`, `api.`) en vez de comprar uno nuevo o usar IP pelada. | Usar únicamente la IP del VPS sin dominio (no viable: Let's Encrypt no emite certificados para IPs). | El operador confirmó que ya posee un dominio; los subdominios son gratis (solo registros DNS) y permiten separar servicios sin coste adicional. |

## Risks

| Riesgo | Mitigación |
|--------|------------|
| El operador nunca ha administrado una VPS antes ("no tengo claro cómo funciona una VPS") — riesgo de mala configuración de seguridad (SSH, firewall) o de downtime no detectado, justo la preocupación explícita que motivó este spec ("que no se caiga nunca"). | El plan de implementación (`/ai-plan`) debe incluir explícitamente: hardening SSH (solo clave, sin root), firewall (ufw), `restart: always`/healthchecks en Docker para autorecuperación de procesos caídos, y monitorización de uptime (aviso externo tipo UptimeRobot). No hay garantía de "cero caídas" — se documenta como objetivo de mejor esfuerzo, no una garantía absoluta. |
| El scraper corriendo desde una IP de datacenter (VPS) puede ser bloqueado con más agresividad por pisos.com/idealista (DataDome) que desde una IP residencial — riesgo aceptado conscientemente en D-007-09. | No se resuelve en este spec (ver Non-Goals). Si se materializa tras el despliegue, es un spec de seguimiento (proxies residenciales, rotación de IP, ajuste de rate/headers). Se debe monitorizar la tasa de éxito del scraper tras la migración para detectar el problema pronto. |
| Migración one-time del histórico (D-007-10) puede introducir inconsistencias (formatos de JSON que cambiaron con el tiempo, campos ausentes en pasadas antiguas) al cargarse en un esquema relacional más estricto que JSON suelto. | El script de migración debe tolerar campos opcionales/ausentes de forma explícita (mismo patrón que `datos_insuficientes` ya usa el sistema actual) y reportar recuento de filas migradas vs. filas con datos incompletos, para verificación manual antes de dar la migración por buena. |
| Nginx + Certbot requieren renovación manual/gestionada de certificados (a diferencia de Caddy, descartado en D-007-08) — riesgo de que el certificado expire si no se automatiza el cron de renovación de Certbot. | El plan de implementación debe incluir explícitamente el cron/systemd timer de renovación automática de Certbot como parte del despliegue, no como paso manual opcional. |
| Backend nuevo (auth, sesiones, contraseñas) introduce superficie de seguridad que no existía en la app estática actual. | Usar librerías estándar y mantenidas para hashing de contraseñas (p.ej. `passlib`/`argon2`) y tokens de sesión — no implementar criptografía a medida. El plan debe incluir un paso de seguridad explícito (rate limiting en login, hashing correcto) antes de exponer el sistema de invitación al grupo cerrado. |
