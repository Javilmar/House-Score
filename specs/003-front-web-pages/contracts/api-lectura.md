# Contrato: lo que el front consume de la API

La forma de las respuestas es la de la spec 001 (`specs/001-backend-api-bbdd/contracts/api.md`);
este documento fija solo lo que cambia o lo que el front exige.

## Origen y CORS

- Base URL: `VITE_API_URL` (build). Por defecto en desarrollo: `http://127.0.0.1:8000`.
- La API responde `Access-Control-Allow-Origin` solo para los orígenes de
  `CORS_ORIGINS` (lista separada por comas). Métodos permitidos: `GET`.
  Sin credenciales.
- Un origen no listado no recibe la cabecera: el navegador bloquea la lectura.
- `POST /ingest` no tiene CORS (no se llama desde navegador).

## GET /listings?incluir_retirados=true

Usado al cargar. Lista completa (activos y retirados). Campos que el front
necesita (todos los del contrato 001, incluido `detalle`): ver la tabla de
mapeo en `inventario-dashboard.md` §datos, que es la que ya aplica
`api_datos.py` y que `src/api/mapeo.ts` reproduce campo a campo.

## GET /historico

Usado por "Evolución y análisis". Lista de pasadas diarias
(`fecha`, `total_listings`, `score_medio`, `precio_medio`, `precio_min`,
`precio_max`).

## Errores que el front distingue

| Situación | Detección | Estado en la UI |
|---|---|---|
| API dormida | sin respuesta > 3 s | "Despertando el servidor…" (sigue esperando) |
| Sin respuesta | 90 s sin respuesta o fallo de red/CORS | aviso "API no disponible" + URL + Reintentar |
| Límite de peticiones | HTTP 429 | aviso "Demasiadas peticiones" + Reintentar, sin reintento automático |
| Error del servidor | HTTP ≥ 400 (≠ 429) | aviso con el código + URL + Reintentar |
| Datos ilegibles | JSON inválido o sin forma de lista | aviso "Respuesta ilegible" + URL |
| Sin listings | `[]` | "Sin datos todavía", distinto de los anteriores |
