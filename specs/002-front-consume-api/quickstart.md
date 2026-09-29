# Guía de Validación (Quickstart): El dashboard consume la API

Valida de extremo a extremo que el dashboard funciona leyendo de la API.

## Prerrequisitos

- Backend en marcha con datos: `cd backend && docker compose up -d` y, la primera
  vez, `docker compose exec -T api python -m scripts.migrar_datos_existentes`
  (ver `backend/README.md`).
- `pip install -r frontend/requirements.txt`.

## Arranque

```bash
cd frontend/dashboard
streamlit run app.py
```

Sin más configuración consulta `http://127.0.0.1:8000`. Para otra API:
`HOUSESCORE_API_URL=http://otra-direccion:8000 streamlit run app.py`.

## Escenario 1 — Datos vivos de la API (Historia 1)

Abrir el dashboard y comparar con la API:

```bash
curl -s "http://127.0.0.1:8000/historico" | python -c "import sys,json; print(json.load(sys.stdin)[-1])"
```

**Resultado esperado**: el gráfico de evolución y los KPIs (listings activos,
score medio) coinciden con el último día del histórico (hoy 2026-09-29), no con
los del 2026-09-08. Las pestañas, filtros, tablas, cards y el desglose de score
se ven como antes. Un listing con datos insuficientes aparece como "sin
valorar".

## Escenario 2 — Nada de ficheros (SC-006)

```bash
grep -n "listings.json\|historico_diario.json\|DATA_DIR" frontend/dashboard/app.py
```

**Resultado esperado**: sin resultados. Además, renombrar temporalmente
`frontend/datos/` no cambia nada en el dashboard.

## Escenario 3 — API caída (Historia 2)

```bash
cd backend && docker compose stop api
```

Recargar el dashboard. **Resultado esperado**: aviso claro con la dirección
consultada y ninguna cifra ni tabla. Arrancar de nuevo la API
(`docker compose start api`) y recargar: se recupera sin reiniciar Streamlit.

## Escenario 4 — Dirección configurable (Historia 3)

Arrancar con `HOUSESCORE_API_URL=http://localhost:9999` (nada escuchando).
**Resultado esperado**: el aviso menciona `http://localhost:9999`.

## Escenario 5 — Rendimiento (SC-004)

Con ~2.000 listings, medir hasta que aparecen los KPIs.
**Resultado esperado**: menos de 5 s en la primera carga.

## Tests automatizados

```bash
python -m pytest frontend/dashboard/tests -q
```

**Resultado esperado**: pasan los tests del adaptador (`test_api_datos.py`) y de
la app completa contra una API falsa (`test_app_api.py`).
