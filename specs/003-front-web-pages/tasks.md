---

description: "Tareas del front web en la nube (Fase 3)"
---

# Tareas: Front web en la nube (Fase 3)

**Entrada**: Documentos de diseño en `/specs/003-front-web-pages/`

**Prerrequisitos**: plan.md, spec.md, research.md, data-model.md, contracts/, inventario-dashboard.md

**Tests**: obligatorios (Principio IV, FR-014). En cada pareja, la tarea de test va primero y DEBE fallar antes de implementar.

**Paridad**: cada tarea de vista o de dominio se valida contra `inventario-dashboard.md`; los valores (umbrales, rangos, textos, colores) se copian de ahí, no se reinventan.

## Formato: `[ID] [P?] [Story] Descripción`

Rutas: front en `frontend/web/`, API en `backend/`.

---

## Fase 1: Configuración

- [X] T001 Crear `frontend/web/` con Vite + React + TypeScript estricto (`package.json`, `tsconfig.json`, `vite.config.ts`, `index.html`, `src/main.tsx`) y scripts `dev`, `build`, `preview`, `typecheck`, `test`, `test:e2e`, `test:smoke`; `.nvmrc` = 22
- [X] T002 [P] Configurar Vitest + Testing Library + jsdom (`vitest.config.ts`, `tests/setup.ts`) y Playwright (`playwright.config.ts`, servidor `vite preview`, API simulada por interceptación de rutas)
- [X] T003 [P] Copiar los assets del mapa a `frontend/web/public/assets/` y mover `frontend/dashboard/scripts/build_mapa_assets.py` a `frontend/scripts/` escribiendo en esa carpeta
- [X] T004 [P] Crear `frontend/web/tests/fixtures/listings.json` e `historico.json` a partir de una respuesta real de la API (anonimizada no es necesario: datos públicos), con al menos un listing retirado, uno sin datos suficientes, uno con bajada y uno nuevo

---

## Fase 2: Fundacional (bloquea todas las historias)

- [X] T005 [P] Test: `tests/unit/mapeo.test.ts` — cada campo de `ListingApi` se traduce a la columna de `app.py` según la tabla de `api_datos.py` (inventario §datos), incluidos los opcionales ausentes
- [X] T006 Implementar `src/api/mapeo.ts` (pasa T005)
- [X] T007 [P] Test: `tests/unit/cliente.test.ts` — clasificación de errores (red, 90 s, 429, ≥400, JSON ilegible, `[]`) y aviso "despertando" a los 3 s (temporizadores falsos), sin reintentos automáticos (contracts/api-lectura.md)
- [X] T008 Implementar `src/api/cliente.ts` y `src/state/carga.ts` (máquina de estados de data-model.md; pasa T007)
- [X] T009 [P] Test: `tests/unit/router.test.ts` — parseo y serialización de las 8 rutas y sus parámetros; ruta desconocida → `#/listados` (contracts/vistas.md)
- [X] T010 Implementar `src/state/router.ts` (pasa T009)
- [X] T011 [P] Estilos base en `src/styles/`: paleta, `SCORE_SCALE`, tipografías Fraunces/Inter/JetBrains Mono, fondo de puntos, clases de cards, KPI, chips, badges, desglose `sb-*` y tabla (valores literales de inventario §base 4)
- [X] T012 [P] Test + implementación de `src/components/Icon.tsx` con los 12 iconos Lucide de `app.py:68-82` (nombre desconocido → svg vacío)
- [X] T013 Implementar el armazón `src/App.tsx`: cabecera, barra de pestañas en el orden de `app.py:1121` ligada al router, contenedor de estados de carga

**Punto de control**: datos cargados y mapeados, rutas funcionando, estilo base aplicado.

---

## Fase 3: Historia 1 — Consultar los pisos desde cualquier sitio (P1) 🎯 MVP

**Test independiente**: con la API simulada, `#/listados` muestra KPIs, filtros combinativos, tabla ordenable, desglose, "sin valorar", retirados y CSV.

- [X] T014 [P] [US1] Test: `tests/unit/derivaciones.test.ts` — `clean`, `zona`, `tipo_vivienda`, €/m², días en mercado, retirado, `score_color` con los casos límite del inventario
- [X] T015 [US1] Implementar `src/domain/derivaciones.ts` (pasa T014)
- [X] T016 [P] [US1] Test: `tests/unit/desglose.test.ts` — `parse_score_details` / `breakdown_score_details` con las reglas y categorías literales del inventario §datos
- [X] T017 [US1] Implementar `src/domain/desglose.ts` y `src/components/Breakdown.tsx` (pasa T016)
- [X] T018 [P] [US1] Test: `tests/unit/kpis.test.ts` — las 6 fórmulas de KPI de cabecera
- [X] T019 [US1] Implementar `src/domain/kpis.ts` y `src/components/KpiBar.tsx` (pasa T018)
- [X] T020 [P] [US1] Test: `tests/unit/filtros.test.ts` — orden combinativo de filtros (zona restringe municipios, etc.), rangos por defecto, "mostrar retirados", y rendimiento: filtrar y ordenar 2.000 listings < 200 ms (SC-006)
- [X] T021 [US1] Implementar `src/domain/filtros.ts` (pasa T020)
- [X] T022 [P] [US1] Test: `tests/components/Listados.test.tsx` — columnas, ordenación por cabecera, badges (retirado, s/valorar), enlace al anuncio en pestaña nueva, botones ↗ y €, estado vacío y CSV (columnas y nombre `listings_<fecha>.csv`)
- [X] T023 [US1] Implementar `src/views/Listados.tsx` y `src/domain/csv.ts` (pasa T022)
- [X] T024 [US1] Test e2e `tests/e2e/listados.spec.ts`: cargar, filtrar, ordenar, desplegar desglose, descargar CSV, vista estrecha (390 px)

**Punto de control**: la Historia 1 funciona sola contra la API simulada.

---

## Fase 4: Historia 2 — Aviso claro cuando la API está dormida o caída (P1)

**Test independiente**: con la API simulada retrasada o fallando, el front muestra cada estado y se recupera con "Reintentar".

- [X] T025 [P] [US2] Test: `tests/components/EstadoCarga.test.tsx` — "Despertando el servidor…", avisos por tipo con la URL consultada, "Sin datos todavía", ninguna cifra en estado de error, botón Reintentar
- [X] T026 [US2] Implementar `src/components/EstadoCarga.tsx` (pasa T025)
- [X] T027 [US2] Test e2e `tests/e2e/estados.spec.ts`: respuesta retrasada 10 s, 503, 429, JSON roto, `[]`, recuperación tras Reintentar

---

## Fase 5: Historia 3 — El scorer publica en la nube (P1)

**Test independiente**: la API acepta lecturas solo desde los orígenes permitidos, rechaza escrituras sin secreto y el scorer espera a que la API despierte.

- [X] T028 [P] [US3] Test: `backend/tests/contract/test_cors.py` — origen permitido recibe `Access-Control-Allow-Origin` en `GET /listings` y `/historico`; origen no permitido no; preflight de `POST` no permitido
- [X] T029 [US3] Implementar `cors_origins` en `backend/app/core/config.py` y `CORSMiddleware` en `backend/app/main.py` (pasa T028)
- [X] T030 [P] [US3] Test: `backend/tests/unit/test_publicar.py` — `verificar_api` reintenta con espera creciente hasta el límite (~3 min) y aborta con mensaje claro al agotarlo
- [X] T031 [US3] Implementar los reintentos en `backend/worker/scraper/publicar.py` (pasa T030)
- [X] T032 [P] [US3] Test: `backend/tests/unit/test_hermes_launcher.py` — con la API dormida al empezar, el lanzador espera en vez de abortar; el mensaje de error ya no remite a `docker compose up -d`
- [X] T033 [US3] Implementar la espera en `backend/ops/hermes_launcher.py` (pasa T032)
- [X] T034 [US3] `backend/Dockerfile`: uvicorn con `--proxy-headers --forwarded-allow-ips='*'` (research §7). Verificación por ejecución (precedente: T051 de la spec 001): en T036, una petición desde dos IPs distintas consume cupos distintos
- [X] T035 [US3] Adaptar `backend/ops/backup.ps1` para volcar Neon con `pg_dump -Fc` desde `postgres:18-alpine` (research §11) y documentarlo en `backend/README.md`. Verificación por ejecución: restaurar el backup en una base vacía y comparar recuentos por tabla con Neon _(2026-10-21: backup de Neon de 483 KB restaurado en una base vacía: listing 2359, historial_precio 259, pasada_diaria 50, alembic_version 1)_
- [ ] T036 [US3] Desplegar la API en Render (raíz `backend`, Docker, variables `DATABASE_URL`, `DATABASE_URL_UNPOOLED`, `INGEST_SECRET`, `CORS_ORIGINS`, `PORT=8000`) y ejecutar quickstart §3, incluida la verificación de que el rate limit ve la IP real del cliente

---

## Fase 6: Historia 4 — El histórico existente no se pierde (P1)

- [X] T037 [US4] Crear `backend/ops/migrar_a_neon.ps1`: restaura el volcado en un PostgreSQL efímero local, cuenta filas por tabla, restaura en Neon por la conexión directa (`pg_restore --no-owner --no-privileges --clean --if-exists`) y compara recuentos; falla si difieren. Verificación por ejecución: la propia comparación de recuentos (T038)
- [X] T038 [US4] Ejecutar la migración con `housescore-2026-10-21_1354.dump` y anotar los recuentos en quickstart §2 (SC-005) _(2026-10-21: listing 2359, historial_precio 259, pasada_diaria 50, precio_referencia 0, alembic_version 1; idénticos en volcado y Neon `production`. Última pasada del volcado: 2026-10-14)_

---

## Fase 7: Historia 5 — Las mismas vistas que hoy (P2)

Cada vista: test de componente primero (contenido, controles, valores por defecto y estados vacíos del inventario), luego la vista.

- [X] T039 [P] [US5] Test + implementación `src/views/Top.tsx` y `src/components/ListingCard.tsx` (slider 5–30, por defecto 15; card completa; desplazamiento a `id`)
- [X] T040 [P] [US5] Test + implementación `src/views/Novedades.tsx` (criterio de "nuevo" del inventario §tabs2)
- [X] T041 [P] [US5] Test: `tests/unit/graficos.test.ts` — las especificaciones de figura de Evolución (eje dual, precios, histograma 20 bins, top-10 ubicaciones) y mínimo de 2 días con su mensaje
- [X] T042 [US5] Implementar `src/domain/graficos.ts` y `src/views/Evolucion.tsx` con Plotly cargado bajo demanda (pasa T041)
- [X] T043 [P] [US5] Test + implementación `src/views/Bajadas.tsx` (orden, % de bajada, precio tachado)
- [X] T044 [P] [US5] Test: `tests/unit/hipoteca.test.ts` — `calc_impuestos` y `calc_hipoteca` con los valores de `app.py` (ITP 6 %/9 %, IVA 10 %, AJD 0,75 %/1,5 %, otros 1,5 % + 400 €) y casos límite; gastos mensuales y umbrales de ratio 30 %/40 %
- [X] T045 [US5] Implementar `src/domain/hipoteca.ts` y `src/views/Hipoteca.tsx` con precarga desde la ruta una sola vez (pasa T044)
- [X] T046 [P] [US5] Test + implementación `src/views/ComoFunciona.tsx` (bloques de scoring y 6 desplegables con su texto)
- [X] T047 [P] [US5] Test: `tests/unit/mapas.test.ts` — figuras de criminalidad y renta (escala, rango, `zoom`, `center`, estilo), join con `cod_ine` normalizado a texto, municipios sin dato en gris, rankings
- [X] T048 [US5] Implementar `src/domain/mapas.ts` y `src/views/Mapas.tsx` con carga diferida de assets y Plotly (pasa T047)
- [X] T049 [US5] Test e2e `tests/e2e/navegacion.spec.ts`: las 8 pestañas, ↗ a Top, € a Hipoteca precargada desde Listados, Top, Novedades y Bajadas; recargar conserva la vista. Se ejecuta a 1280 px y a 390 px de ancho (edge case móvil)

---

## Fase 8: Despliegue, corte y cierre

- [ ] T050 Desplegar el front en Cloudflare Pages (raíz `frontend/web`, `npm run build`, salida `dist`, `VITE_API_URL`, `NODE_VERSION=22`) y añadir su origen a `CORS_ORIGINS` en Render
- [ ] T051 Test de humo `tests/e2e/smoke.spec.ts` contra la URL publicada (solo lectura): carga, 8 pestañas, sin errores de consola
- [ ] T052 Medir SC-002 (primera pantalla < 3 s con la API despierta) en la URL publicada y anotarlo
- [ ] T053 Apuntar el scorer del PC a Render (`HOUSESCORE_API_URL`, `INGEST_SECRET` en `backend/.env`) y ejecutar quickstart §5. Paso previo (Historia 4, escenario 2): si la base local tiene pasadas posteriores al volcado usado en T038, sacar un volcado nuevo y repetir T038 justo antes del cambio
- [ ] T054 Corte (Principio VI): eliminar `frontend/dashboard/` (incluidos `.streamlit/` y sus tests), `frontend/requirements.txt` y `backend/ops/cloudflared.yml`; reescribir `README.md`, `backend/README.md` y la referencia de funcionalidades como `frontend/web/FUNCIONALIDADES.md`; quickstart §6
- [ ] T055 Marcar en `specs/001-backend-api-bbdd/tasks.md` T047 (escenario 6) y T050 como sustituidos por esta spec
- [ ] T056 Enmendar la constitución con `/speckit-constitution`: objetivo de despliegue (Pages + Render + Neon), Fase 3 iniciada, stack del backend decidido
- [ ] T057 Ejecutar quickstart.md completo y comprobar que Neon, Render y Cloudflare Pages siguen en planes gratuitos sin cargos (SC-008)

---

## Dependencias

- Fase 1 → Fase 2 → Historias.
- US1 y US2 dependen solo de la Fase 2. US5 depende de US1 (componentes de listing y desglose).
- US3 y US4 (backend) son independientes del front y pueden ir en paralelo con US1/US2.
- T050 depende de T036 (URL de la API) y de US1, US2 y US5 completas. T054 depende de T051 y T053: Streamlit no se borra hasta que el front publicado y el scorer en la nube funcionan.

## Paralelización

- Backend (T028–T038) en paralelo con el front (T014–T049).
- Dentro de US5, las vistas T039, T040, T043, T046 y las parejas T041/T042, T044/T045, T047/T048 son independientes entre sí.
