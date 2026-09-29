# Guía de Validación (Quickstart): Backend HouseScore

Valida de extremo a extremo que el backend funciona, usando el entorno
local reproducible (Historia 3 / SC-003).

## Prerrequisitos

- Docker Desktop y Docker Compose instalados.
- Checkout limpio de este repositorio.
- Para el Escenario 6 (arranque tras reinicio): Docker Desktop configurado
  para iniciarse con Windows.

## Arranque

```bash
cd backend
docker compose up --build
```

Debe quedar operativo en menos de 5 minutos (SC-003), sin ningún paso de
configuración manual: las migraciones de Alembic corren automáticamente al
arrancar el servicio `api`.

## Escenario 1 — La API sirve listings ya puntuados (Historia 1)

```bash
curl http://localhost:8000/listings | jq '.[0]'
```

**Resultado esperado**: un listing con `score` calculado y
`datos_insuficientes` presente (verdadero o falso). Ningún campo requiere
tocar `frontend/datos/`.

## Escenario 2 — El scraper guarda una pasada sin git (Historia 2)

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Authorization: Bearer $INGEST_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"listings": [{"url": "https://ejemplo/piso-1", "titulo": "Piso de prueba", "precio": 200000, "m2": 70, "habitaciones": 2, "banos": 1, "municipio": "Alcorcón", "fuente": "pisos.com", "score": 65.0}]}'

curl http://localhost:8000/listings?municipio=Alcorc%C3%B3n | jq '.[] | select(.url=="https://ejemplo/piso-1")'
```

**Resultado esperado**: el listing de prueba aparece inmediatamente en
`GET /listings`, sin ningún commit ni push a este repositorio.

Repetir la misma llamada `POST /ingest` una segunda vez y comprobar que
**no** aparece duplicado (SC-005) — debe seguir habiendo un único listing
con esa `url`.

## Escenario 3 — Endpoint de ingesta protegido (FR-010/FR-011)

```bash
curl -i -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"listings": []}'
```

**Resultado esperado**: `401 Unauthorized` — sin la cabecera `Authorization`
correcta, el endpoint de escritura rechaza la petición.

Con el Cloudflare Tunnel activo, repetir la petición contra la URL pública
del túnel: **Resultado esperado**: `404` (la ruta no está publicada),
incluso enviando el secreto correcto.

## Escenario 4 — Histórico agregado disponible (FR-013)

```bash
curl http://localhost:8000/historico | jq '.[-1]'
```

**Resultado esperado**: el día de la última pasada aparece con sus
métricas agregadas (`total_listings`, `score_medio`, ...).

## Escenario 5 — Rate limiting en lectura (FR-012)

```bash
for i in $(seq 1 200); do curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/listings; done | sort | uniq -c
```

**Resultado esperado**: a partir de cierto número de peticiones en la
ventana configurada, empiezan a aparecer respuestas `429`.

## Escenario 6 — Arranque automático y copia de seguridad (FR-015/FR-016)

1. Reiniciar el PC sin abrir ninguna terminal y, pasados unos minutos,
   ejecutar `curl http://localhost:8000/listings`. **Resultado esperado**:
   responde 200 con los datos previos al reinicio (SC-006).
2. Comprobar que la tarea programada del scraper figura como pendiente o
   ejecutada, y que si se perdió su hora se lanza al volver a encender el
   equipo.
3. Ejecutar la copia de seguridad, restaurarla en una base de datos limpia
   y comprobar que `GET /listings` devuelve los mismos datos (SC-007).

## Tests automatizados

```bash
docker compose --profile test run --rm test
```

**Resultado esperado**: toda la suite (contract + integration + unit) pasa
en verde contra el entorno local, sin tocar ningún dato de producción
(Historia 3, escenario 2).
