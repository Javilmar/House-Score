# Quickstart: validar el front web en la nube

Escenarios de validación de punta a punta. Cada uno indica qué historia o
criterio cubre.

## Requisitos

- Node 22, Docker, Python 3.11.
- `.env.local` en la raíz (de `neon deploy`) y `backend/.env` con `INGEST_SECRET`.
- Servicios: API en Render (`https://<servicio>.onrender.com`), front en
  Cloudflare Pages (`https://<proyecto>.pages.dev`).

## 1. Desarrollo local

```bash
cd backend && docker compose up -d                 # API local en :8000 (BD local de pruebas)
cd frontend/web && npm ci && npm run dev           # front en http://localhost:5173
npm test && npm run test:e2e                       # Vitest + Playwright (API simulada)
```

Esperado: tests en verde; el front en :5173 muestra las 8 vistas con la API local.

## 2. Migración del histórico (Historia 4, SC-005)

```bash
backend/ops/migrar_a_neon.ps1 -Dump C:\Users\LWD12\Downloads\housescore-2026-10-21_1354.dump
```

Esperado: imprime recuentos por tabla del volcado y de Neon, y son iguales.

## 3. API en Render (Historia 3, FR-006, FR-007)

```bash
curl -s -o /dev/null -w "%{http_code}\n" https://<api>/listings                 # 200 (puede tardar ~1 min si dormía)
curl -s -I -H "Origin: https://<front>.pages.dev" https://<api>/listings | grep -i access-control-allow-origin   # presente
curl -s -I -H "Origin: https://evil.example" https://<api>/listings | grep -ci access-control-allow-origin      # 0
curl -s -o /dev/null -w "%{http_code}\n" -X POST https://<api>/ingest -d '{}'  # 401
```

## 4. Front publicado (Historias 1, 2 y 5; SC-001 a SC-003)

1. Con el PC apagado (o sin la API local), abrir `https://<front>.pages.dev`.
2. Si la API dormía: aparece "Despertando el servidor…" y luego los datos.
3. Comprobar KPIs, filtros combinativos, desglose, "sin valorar", retirados,
   CSV, botón de hipoteca precargada y las 8 vistas.
4. `npm run test:smoke -- --base-url https://<front>.pages.dev` (Playwright
   contra producción, solo lectura).

## 5. Scorer contra la nube (Historia 3, SC-004)

```bash
# en el PC del scorer: HOUSESCORE_API_URL=https://<api> en el entorno del lanzador
python backend/ops/hermes_launcher.py
```

Esperado: con la API dormida, el lanzador espera a que despierte y el lote
publica; el front muestra la pasada al recargar.

## 6. Corte de Streamlit (FR-012, SC-007)

```bash
git ls-files frontend/dashboard frontend/requirements.txt   # vacío
grep -rn "streamlit" --include=*.md --include=*.py --include=*.toml . | grep -v specs/   # vacío
```
