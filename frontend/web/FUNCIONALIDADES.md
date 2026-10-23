# House Score — Referencia de funcionalidades (front web)

> **Uso:** fuente de verdad de **qué hace el front** y **cómo está organizado**. Consúltalo
> antes de añadir una funcionalidad para no duplicar lógica y mantener la coherencia visual.
> Contrato de rutas: [`specs/003-front-web-pages/contracts/vistas.md`](../../specs/003-front-web-pages/contracts/vistas.md).
>
> **Nota sobre referencias `app.py:LINE`:** los comentarios del código citan líneas de
> `frontend/dashboard/app.py`, el dashboard Streamlit original. Ese fichero ya no está en el
> repo: esas referencias apuntan a la etiqueta git **`pre-retirada-streamlit`**
> (`git show pre-retirada-streamlit:frontend/dashboard/app.py`).

---

## 1. Visión general

Front estático (React 19 + Vite + TypeScript, gráficos con `plotly.js-dist-min`) desplegado como
Cloudflare Worker de ficheros estáticos en <https://housescore.errinostrich.workers.dev>. No tiene
servidor propio: el navegador pide los datos a la API de Render (`VITE_API_URL`, por defecto
`http://127.0.0.1:8000`).

```
scorer (PC, hermes)  →  POST /ingest  →  API (Render)  →  Neon
                                           └─ GET /listings?incluir_retirados=true, GET /historico  →  front
```

- Precio máximo scrapeado según zona: **300.000 €** (Madrid Sur, Madrid Sureste, Toledo Norte),
  **350.000 €** (Madrid Este) y **400.000 €** (Madrid Norte).
- Fuentes: **pisos.com** (las 5 zonas) y **fotocasa.es** (las 4 zonas de Madrid; no Toledo Norte).
- Zonas: Madrid Sur (18 municipios), Madrid Este (6: Torrejón de Ardoz, Alcalá de Henares, Coslada,
  San Fernando de Henares, Mejorada del Campo, Velilla de San Antonio), Madrid Sureste (5: Rivas-Vaciamadrid,
  Arganda del Rey, San Martín de la Vega, Campo Real, Morata de Tajuña), Madrid Norte (6: Tres Cantos,
  Colmenar Viejo, Alcobendas, San Sebastián de los Reyes, Algete, San Agustín del Guadalix) y Toledo Norte
  (Esquivias, Illescas, Seseña, Ugena, Yeles). La zona se deriva en `src/domain/derivaciones.ts`.
  **Toledo capital excluida**; los demás municipios toledanos se filtran en la API
  (`backend/app/services/reglas.py`).
- Antes de guardar, el scraper descarta los anuncios «sin posesión», okupados/ocupados, de nuda propiedad y
  las subastas: no aparecen en ninguna vista (ya no hay penalización por «ocupada» en el scoring).
- Scoring 0–100 en `backend/worker/scraper/property_scorer_common.py` (explicado en la vista
  «Cómo funciona»). Un listing sin m² fiable (`datos_insuficientes`) queda «sin valorar»: no entra en
  el score medio de los KPI.

### Carga y errores

Al abrir, el front lanza `GET /listings?incluir_retirados=true` y `GET /historico` a la vez
(`src/state/carga.ts`; sin reintentos automáticos, timeout de 90 s). Estados (`EstadoCarga.tsx`):

| Estado | Cuándo | Qué se ve |
|---|---|---|
| `cargando` | petición en curso | «Cargando…» |
| `despertando` | sin respuesta a los 3 s (Render duerme la API gratuita, ~1 min) | «Despertando el servidor…» |
| `sin_datos` | la API responde con 0 listings | «Sin datos todavía» + Reintentar |
| `error` | `no_disponible`, `limite` (429), `http`, `ilegible` | título del error, dirección consultada y Reintentar |
| `listo` | datos recibidos | KPI + vista |

Desde `error` no hay transiciones automáticas: solo el botón **Reintentar**. El pie de página
muestra la hora de carga, la URL de la API y «Forzar recarga».

---

## 2. Navegación (rutas por hash)

Las 9 vistas, en este orden, con ruta `#/<vista>?<parámetros>`. Recargar restaura vista y parámetros;
ruta desconocida o vacía → `#/listados`.

| # | Vista | Ruta | Parámetros |
|---|---|---|---|
| 1 | Listados completos | `#/listados` | `zona`, `muni` (repetibles), `score=min-max`, `precio=min-max`, `hab=min-max`, `retirados=1` |
| 2 | Top scoring | `#/top` | `n` (5–30, por defecto 15), `id` (url del listing a resaltar) |
| 3 | Novedades | `#/novedades` | — |
| 4 | Evolución y análisis | `#/evolucion` | — |
| 5 | Bajadas de precio | `#/bajadas` | `orden` |
| 6 | Hipoteca | `#/hipoteca` | `precio`, `tipo` (`segunda-mano`\|`obra-nueva`), `ccaa` (`madrid`\|`clm`) |
| 7 | Cómo funciona | `#/como-funciona` | — |
| 8 | Mapas | `#/mapas` | `capa` (`criminalidad`\|`renta`\|`precio`) |
| 9 | Favoritos | `#/favoritos` | — |

Navegación entre vistas:

- Botón **↗** en Listados → `#/top?id=<url>`: abre Top scoring, hace scroll al card y lo resalta
  1,8 s si está entre los N mostrados.
- Botón **€ Hipoteca** (Listados, Top, Novedades, Bajadas) →
  `#/hipoteca?precio=…&tipo=…&ccaa=…`: la calculadora se rellena una vez; los cambios posteriores del
  usuario no se pisan.
- Los filtros de Listados se escriben en el hash al cambiarlos (enlace compartible, sin recargar).

---

## 3. KPI de la cabecera (siempre visibles)

`src/domain/kpis.ts`, componente `KpiBar`.

Todos los KPI se calculan sobre los listings activos (los retirados no cuentan).

| KPI | Descripción |
|---|---|
| Total listings | Listings activos |
| Nuevos hoy | Activos con `first_seen == hoy` |
| Score medio | Media de los activos con m² fiable (si no hay ninguno, de todos los activos); `—` sin datos |
| Precio medio | Media de los listings activos |
| Bajadas | Activos con `price_drop > 0` |
| Sin valorar | Activos con `datos_insuficientes = true` |

---

## 4. Vistas

### 4.1 Listados completos (`views/Listados.tsx`)

Tabla ordenable con todos los listings (más los retirados si se activa «Mostrar retirados»).

- **Filtros combinativos** (cada uno reduce las opciones de los siguientes): Zona, Municipio, rango de
  score (0–100), rango de precio (€), habitaciones. Los rangos sin recorrido no se muestran.
- **Columnas** (clic en cabecera = ordenar; Enter/Espacio también): Título (enlace al anuncio), Precio,
  Score (barra + desglose), €/m², m², Tipo (Obra nueva / Segunda mano), Fuente, Ubicación, Días en
  mercado.
- **Acciones por fila:** título → anuncio en pestaña nueva; **↗** → Top scoring; **€** → Hipoteca;
  insignia «s/valorar» si no hay m² fiable; **★/☆** → guarda o quita el anuncio de favoritos.
- **Descargar CSV** con los listings filtrados (`domain/csv.ts`).

### 4.2 Top scoring (`views/Top.tsx`)

Cards expandibles de los N mejores (slider «Mostrar top», 5–30, por defecto 15). Cada card: insignia
de score con color semántico, título enlazado, posición, metadatos (ubicación, planta, año, certificado
energético), precio, €/m², m², habitaciones, baños, chips de características (verde) y penalizaciones
(rojo), desglose del score, descripción (truncada a 1500 caracteres) y botón **€ Hipoteca**.

### 4.3 Novedades (`views/Novedades.tsx`)

Pisos nuevos por pasada: selector «Pasada» (fechas distintas de `first_seen`, la más reciente primero) y
«Ordenar por» (Mejor score · Precio más bajo · Mayor superficie · Más antiguo). Contador de pisos
nuevos y cards compactas con botón **€ Hipoteca**. Sin fechas: «No hay datos de ejecuciones disponibles».

### 4.4 Evolución y análisis (`views/Evolucion.tsx`)

Gráficos Plotly (`domain/graficos.ts`):

- **Evolución diaria** (eje dual): barras de nº de listings + línea de score medio.
- **Evolución de precios**: media, mínimo y máximo por día.
  Ambos requieren ≥ 2 días de histórico; si no, un aviso lo indica.
- **Distribución de scores**: histograma (20 bins).
- **Top ubicaciones**: barras horizontales, top 10 por nº de anuncios.

### 4.5 Bajadas de precio (`views/Bajadas.tsx`)

Cards compactas de los listings con `price_drop > 0` (detectado por la API en cada ingesta): precio
anterior tachado → actual, insignia `−X%`, días en mercado y botón **€ Hipoteca**. Selector «Ordenar
por»: Mayor bajada (€) (por defecto) · Mayor bajada (%) · Mejor score · Precio más bajo · Más reciente
(parámetro `orden`). Sin bajadas: aviso informativo.

### 4.6 Hipoteca (`views/Hipoteca.tsx`, `domain/hipoteca.ts`)

Calculadora, pre-cargable desde cualquier listing.

- **Entradas:** precio de compra, tipo (Segunda mano / Obra nueva), comunidad (C. Madrid /
  Castilla-La Mancha), entrada (%), plazo (5–40 años), tipo de interés fijo (%). Valores por defecto:
  entrada 20 %, 30 años, 3 %.
- **Resultados:** cuota mensual (anualidad francesa), ahorro necesario (entrada + impuestos + gastos),
  total de intereses, total desembolsado, y tabla de desglose.
- **Gastos mensuales y esfuerzo:** sliders de comunidad, IBI, seguro, luz + gas, internet e ingresos
  netos; muestra coste mensual total y % de esfuerzo sobre ingresos (verde < 30 %, naranja < 40 %,
  rojo ≥ 40 %).

**Constantes de fiscalidad (2024-2026), todas en `domain/hipoteca.ts`:**

| Concepto | Madrid | Castilla-La Mancha |
|---|---|---|
| ITP (segunda mano) | 4 % | 9 % |
| AJD (obra nueva) | 0,75 % | 1,5 % |
| IVA obra nueva | 10 % | 10 % |
| Otros gastos | 1,5 % del precio + 400 € de tasación | igual |

### 4.7 Cómo funciona (`views/ComoFunciona.tsx`)

Documentación inline: tabla del scoring por bloques (Valor vs zona, Superficie, Señales de mercado,
Características, Extras, Penalizaciones) y expanders de FAQ (portales de origen, municipios, verificación
de precios, «barato para su zona», «sin valorar», origen de los datos del mapa).

### 4.8 Mapas (`views/Mapas.tsx`, `domain/mapas.ts`)

Mapas coropléticos Plotly con selector de capa (parámetro `capa`). Las capas con assets disponibles
son las que se ofrecen; `precio` siempre se ofrece. Si faltan los assets de criminalidad y renta, un
aviso indica `python frontend/scripts/build_mapa_assets.py`.

| Capa | Dato | Geometría | Notas |
|---|---|---|---|
| `criminalidad` | Tasa oficial (infracciones penales × 100.000 hab), Ministerio del Interior, Q1 anualizado | `municipios_zona.geojson` (47 municipios, clave `cod_ine`) | Solo los 12 municipios > 20.000 hab tienen dato; el resto, gris (desplegable con la lista). Verde (bajo) → rojo (alto). Ranking de peligrosidad. `zoom=9` |
| `renta` | Renta neta media por persona, ADRH 2023 (INE) | `secciones_renta.geojson` (953 secciones, clave `cusec`) | Escala invertida: rojo (baja) → verde (alta). Permite ver diferencias dentro de cada municipio. Aviso: renta ≠ criminalidad. Ranking de barrios. `zoom=10` |
| `precio` | €/m² mediana por municipio, calculada en el navegador con los listings cargados | `municipios_zona.geojson` | Hover con precio mediano y nº de anuncios; municipios sin anuncios, en gris. Ranking de precio por municipio |

Los assets están en `public/assets/` y se regeneran con `python frontend/scripts/build_mapa_assets.py`
(OpenDataSoft / georef-spain-municipio, Portal Estadístico de Criminalidad, Atlas de Renta de los
Hogares del INE).

### 4.9 Favoritos (`views/Favoritos.tsx`, `state/favoritos.ts`, `components/BotonFavorito.tsx`)

Anuncios marcados con la estrella ☆/★ (botón con `aria-pressed`) en Listados, Top scoring, Novedades y
Bajadas. **Solo viven en el navegador**: `localStorage`, clave `housescore:favoritos`, array JSON de
urls. Sin backend, sin cuenta, sin datos personales; no se comparten entre dispositivos. Almacenamiento
ausente, corrupto o bloqueado → lista vacía (si está bloqueado, los cambios duran hasta recargar).
Se sincroniza entre pestañas abiertas con el evento `storage`.

- La vista lista los favoritos con su tarjeta, **incluidos los retirados** (etiqueta «retirado»).
- Un favorito cuya url ya no está en los datos se muestra como fila mínima con la url y un botón
  «Quitar de favoritos».
- Sin favoritos, un aviso explica que se guardan solo en este navegador.

---

## 5. Diseño

Modo oscuro siempre, un único color de acento, sin emojis en la UI (iconos SVG en
`components/Icon.tsx`, trazados en `iconPaths.ts`). Tokens en `src/styles/tema.ts` (los mismos valores
usa el CSS):

```
ACCENT  #6366f1   acento único          INK     #e4e4e7   texto principal
MUTED   #a1a1aa   texto secundario      SUBTLE  #52525b
BORDER  #27272a                         SURFACE #18181b   tarjetas
GRID    #1f1f23   rejilla de gráficos
```

Escala de score → color: ≥70 `#22c55e` · ≥50 `#84cc16` · ≥35 `#eab308` · ≥20 `#f97316` · ≥0 `#ef4444`.
Tipografías: **Fraunces** (títulos y cifras grandes), **Inter** (texto), **JetBrains Mono** (valores
tabulares). Tema de las figuras Plotly en `styles/plotlyStreamlit.ts`.

---

## 6. Dónde está el código

```
frontend/web/
├── src/
│   ├── api/         cliente.ts (GET + clasificación de errores), mapeo.ts (API → tipos del front)
│   ├── domain/      lógica pura y testeable: filtros, kpis, hipoteca, tarjetas, graficos, mapas,
│   │                desglose, derivaciones, csv
│   ├── state/       carga.ts (máquina de estados), datos.tsx (contexto), router.ts (hash), favoritos.ts (localStorage)
│   ├── views/       una por vista (Listados, Top, Novedades, Evolucion, Bajadas, Hipoteca,
│   │                ComoFunciona, Mapas, Favoritos)
│   ├── components/  KpiBar, ListingCard, Breakdown, Grafico, EstadoCarga, controles, Icon, PiePagina…
│   └── styles/      CSS por vista/componente + tema.ts + plotlyStreamlit.ts
├── public/assets/   geojson y csv de los mapas
├── tests/           unit/ (domain, api, router), components/ (Testing Library), e2e/ (Playwright),
│                    fixtures/
├── wrangler.jsonc   Worker de assets estáticos (SPA fallback sobre dist/)
└── vite.config.ts, vitest.config.ts, playwright.config.ts
```

Regla de oro: la lógica va en `src/domain` (sin React) y se prueba en `tests/unit`; las vistas solo
la componen.

## 7. Comandos

```bash
cd frontend/web
npm ci
npm run dev            # servidor de desarrollo (VITE_API_URL=... para otra API)
npm run typecheck
npm test               # Vitest: unit + components
npm run build          # tsc -b && vite build → dist/
npm run test:e2e       # Playwright con API simulada (sirve el build con vite preview)
BASE_URL=https://housescore.errinostrich.workers.dev npm run test:smoke   # solo lectura, API real

# Regenerar los assets del mapa (desde la raíz del repo)
python frontend/scripts/build_mapa_assets.py
```

## 8. Patrones al añadir funcionalidades

1. **Nueva vista:** añadirla a `VISTAS` en `state/router.ts`, a la navegación de `App.tsx` y a
   `contracts/vistas.md`; reflejarla en «Cómo funciona» si afecta al usuario.
2. **Cálculos:** en `src/domain` como funciones puras con test unitario.
3. **Filtros:** combinativos (los anteriores reducen las opciones de los siguientes) y escritos en el hash.
4. **Fiscalidad:** solo en las constantes de `domain/hipoteca.ts`.
5. **Capas de mapa:** añadir `CapaId` y su figura en `domain/mapas.ts`; la clave de join va en
   `properties` del GeoJSON y en una columna de las filas.
6. **Diseño:** usar los tokens de `tema.ts`; sin colores fuera de la paleta ni emojis en la UI.
7. **Sin dependencias nuevas** salvo justificación explícita.
