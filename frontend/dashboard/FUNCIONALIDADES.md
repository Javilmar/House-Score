# House Score — Referencia de funcionalidades

> **Uso:** este fichero es la fuente de verdad de **qué hace la app** y
> **cómo está estructurada internamente**. Consúltalo siempre antes de
> diseñar o implementar una nueva funcionalidad para no duplicar lógica,
> mantener coherencia visual y reutilizar los patrones establecidos.

---

## 1. Visión general del producto

**House Score** es un dashboard Streamlit para buscar vivienda asequible en la
corona sur de Madrid (Madrid Sur) y norte de Toledo (Toledo Norte). El flujo es:

```
property_scorer.py   →  guardar.py  →  datos/YYYY-MM-DD.json  →  app.py (Streamlit)
(scraper + scoring)     (merge/git)     (ficheros diarios)        (UI)
```

- Precio máximo scrapeado: **≤ 300.000 €**
- Fuentes: **pisos.com** (scraping fiable) + **idealista** (best-effort, puede
  ser bloqueado por DataDome)
- Zona de cobertura: municipios a 30-40 min de Madrid por A-42 / A-4 / A-5
- **Toledo capital excluida** (>55 min, mercado distinto)

---

## 2. Arquitectura de ficheros

```
house-dashboard/
├── dashboard/
│   ├── app.py                  ← UI principal (Streamlit, ~1850 líneas)
│   ├── guardar.py              ← merge de pasadas + git push
│   ├── assets/
│   │   ├── municipios_zona.geojson     ← polígonos municipales (47 mun.)
│   │   ├── criminalidad.csv            ← tasa criminalidad oficial (12 mun.)
│   │   └── secciones_renta.geojson     ← 953 secciones censales + renta ADRH 2023
│   └── scripts/
│       └── build_mapa_assets.py        ← genera los 3 assets del mapa
├── datos/
│   └── YYYY-MM-DD.json         ← una pasada de scraper por día
└── config/
    └── precios_referencia.json ← mediana €/m² por municipio (actualizada cada pasada)
```

### Fuentes de datos externas (APIs públicas)

| Asset | Fuente | Endpoint |
|---|---|---|
| `municipios_zona.geojson` | OpenDataSoft / georef-spain-municipio (CC-BY-4.0) | `public.opendatasoft.com/api/explore/v2.1/…` |
| `criminalidad.csv` | Portal Estadístico de Criminalidad · Ministerio del Interior | Datos manuales (Q1 anualizado) |
| `secciones_renta.geojson` | Atlas Renta Hogares (ADRH 2023) · INE · ArcGIS FS público | `services7.arcgis.com/SEjlCWTAIsMEEXNx/…/ADRH_2023_Renta_media_por_persona/FeatureServer/3` |

---

## 3. Municipios objetivo

### Madrid Sur (18)
Alcorcón · Arroyomolinos · Batres · Ciempozuelos · Cubas de la Sagra ·
Fuenlabrada · Getafe · Griñón · Humanes de Madrid · Leganés · Móstoles ·
Moraleja de Enmedio · Navalcarnero · Parla · Pinto · Serranillos del Valle ·
Torrejón de la Calzada · Valdemoro

### Toledo Norte (5 de interés activo)
Esquivias · Illescas · Seseña · Ugena · Yeles

> El resto de municipios toledanos (Yuncos, Yunclillos, etc.) se filtran
> en `guardar.py` (`_TOLEDO_NORTE_BLOQUEADOS`) antes de persistir.

---

## 4. Sistema de scoring

Cada listing recibe una puntuación **0–100**. Motor en `property_scorer.py`.

| Bloque | Campo clave | Puntos |
|---|---|---|
| 💎 **Valor vs zona** (factor más importante) | €/m² vs mediana del municipio | 0 – ~25 |
| 📐 **Superficie** | m² | +5 (≥80) / +8 (≥100) / +12 (≥120) / +15 (≥140) |
| ✨ **Características** (tope +15) | features[] del anuncio | piscina +15 · garaje +12 · trastero +10 · terraza/patio +10 · ascensor/jardín +5 |
| ➕ **Extras** | title/description | obra nueva +10 · transporte +8 · reformado +5 · construido≥2000 +1-5 · ático +3 · eficiencia A/B/C +2 |
| 📈 **Señales de mercado** | price_drop / days_on_market | bajada precio +1-5 · >45 días −3 · >90 días −5 |
| ⚠️ **Penalizaciones** | keywords | ocupada −30 · zona conflictiva −3 a −20 |

**Nota técnica:** si un listing no tiene m² fiable (`datos_insuficientes=True`),
no se puede calcular €/m² y queda marcado "s/valorar" — sale de la tabla pero
no del Top Score ni del count de KPIs.

La **mediana de referencia** por municipio se actualiza en cada pasada y se
almacena en `config/precios_referencia.json`. Si un municipio tiene <5
anuncios, se usa la media de su zona (Madrid Sur / Toledo Norte).

---

## 5. Pestañas de la UI (`app.py`)

```
tab1  Listados completos
tab2  Top scoring
tab3  Evolución y análisis
tab4  Bajadas de precio
tab5  Hipoteca
tab6  Cómo funciona
tab7  Mapa de seguridad
```

---

### Tab 1 — Listados completos

**Qué hace:** tabla HTML interactiva (ordenable por JS en cliente) con todos los
listings del día combinados con el histórico.

**Filtros disponibles:**
- Zona (Madrid Sur / Toledo Norte)
- Municipio (se restringe a la zona seleccionada — filtros combinativos)
- Rango de score (slider 0-100)
- Rango de precio (€)
- Habitaciones (slider)

**Columnas de la tabla:**
`#` · Título (enlace al anuncio) · Precio · Score (barra visual + desglose
expandible) · €/m² · m² · Tipo (Obra nueva / Segunda mano) · Ubicación ·
Días en mercado · Botones de acción (↗ ir a Top scoring / € hipoteca)

**Acciones por fila:**
- Clic en título → abre el anuncio en nueva pestaña
- Botón `↗` → navega al card de ese listing en Tab 2 (si está en Top 30)
- Botón `€` → pre-carga la calculadora de Tab 5 con precio, tipo y CCAA
- Badge `s/valorar` → listing sin m² fiable (no puntuado por €/m²)

**Exportación:** botón "Descargar CSV" con los listings filtrados.

**Implementación clave:**
- `_TABLA_TEMPLATE` (app.py:~402): HTML+JS con ordenación cliente
- `breakdown_score_details()` (app.py:~649): parsea `score_details[]` en items
- Navegación cross-tab: `sessionStorage._sw_tab` + MutationObserver + query params

---

### Tab 2 — Top scoring

**Qué hace:** cards expandibles de los N mejores listings (slider: 5-30, default 15).

**Contenido de cada card:**
- Badge de score (color semántico)
- Título enlazado · Posición ranking
- Metadatos: ubicación · planta · año construcción · certificación energética
- Precio · €/m² · m² · habitaciones · baños
- Chips de características (verde) y penalizaciones (rojo)
- Desglose score expandible (breakdown items por categoría)
- Descripción del anuncio expandible (truncada a 1500 chars)
- Botón `€ Hipoteca` → navega a Tab 5 pre-cargada

---

### Tab 3 — Evolución y análisis

**Qué hace:** gráficos Plotly de tendencias históricas (requiere ≥2 días de datos).

**Gráficos:**
- **Evolución diaria** (eje dual): barras de nº de listings + línea de score medio
- **Evolución de precios**: media, mínimo y máximo por día (líneas)
- **Distribución de scores**: histograma (20 bins)
- **Top ubicaciones**: barras horizontales top-10 por nº de anuncios

---

### Tab 4 — Bajadas de precio

**Qué hace:** cards de todos los listings que han bajado de precio respecto a
pasadas anteriores (detectado en `guardar.py`).

**Contenido de cada card:**
- Score badge · Título enlazado
- Precio anterior (tachado) → precio actual
- Badge verde con `−X%` de bajada
- Días en mercado
- Botón `€ Hipoteca`

**Detección:** `guardar.py:merge()` compara `price` actual vs histórico y escribe
`price_drop` y `previous_price` en el JSON.

---

### Tab 5 — Hipoteca

**Qué hace:** calculadora financiera completa, pre-cargable desde cualquier listing.

**Inputs:**
- Precio de compra (number input, paso 5.000 €)
- Tipo de vivienda: Segunda mano / Obra nueva
- Comunidad autónoma: C. Madrid / Castilla-La Mancha
- Entrada (%) slider 5-50%
- Plazo (años) slider 5-40
- Tipo interés fijo (%) slider 0.5-8%

**KPIs calculados:**
- Cuota mensual (anualidad francesa)
- Ahorro necesario total (entrada + impuestos + gastos)
- Total intereses del préstamo
- Total desembolso (préstamo + intereses)

**Fiscalidad implementada (2024-2026):**
- Segunda mano: ITP = 6% (Madrid) / 9% (CLM)
- Obra nueva: IVA 10% + AJD = 0.75% (Madrid) / 1.5% (CLM)
- Otros gastos: ~1.5% + tasación 400€ fijos

**Desglose detallado:** tabla entrada + impuestos + otros = ahorro total

**Navegación pre-cargada:** los botones `€ Hipoteca` de Tab 1, Tab 2 y Tab 4
inyectan precio, tipo y CCAA via query params (`hip_precio`, `hip_tipo`,
`hip_ccaa`, `hip_nav_id`) + `sessionStorage._sw_tab=4` para navegación automática.

---

### Tab 6 — Cómo funciona

**Qué hace:** documentación inline del sistema para el usuario.

**Secciones:**
- Tabla visual del scoring por bloques (Valor vs zona, Superficie, etc.)
- Expanders de FAQ:
  - Portales de origen (pisos.com + idealista)
  - Municipios rastreados (Madrid Sur 18 + Toledo Norte 5)
  - Verificación de precios (visita a ficha individual)
  - Significado de "barato para su zona"
  - Significado de "sin valorar"
  - Origen de datos del mapa de seguridad (criminalidad + renta)

---

### Tab 7 — Mapa de seguridad

**Qué hace:** choropleth map (Plotly `px.choropleth_map`) con toggle entre dos vistas.

#### Vista A — Criminalidad (por municipio, por defecto)

- **Dato:** tasa de criminalidad oficial (infracciones penales × 100.000 hab)
- **Fuente:** Portal Estadístico de Criminalidad, Ministerio del Interior, Q1 2026 anualizado
- **Geometría:** `municipios_zona.geojson` (47 municipios, clave `cod_ine`)
- **Cobertura de datos:** solo 12 municipios >20.000 hab — el resto aparece gris
- **Escala de color:** verde (seguro, tasa baja) → rojo (peligroso, tasa alta)
- **Ranking:** tabla de municipios ordenados por tasa
- Eje: `zoom=9`, `center lat=40.18 lon=-3.78`

#### Vista B — Renta por barrio (sección censal)

- **Dato:** renta neta media por persona (€/año), ADRH 2023 INE
- **Fuente:** ArcGIS Feature Service público INE (oct 2025), capa sección censal
- **Geometría + datos:** `secciones_renta.geojson` (953 secciones, clave `cusec`)
- **Cobertura:** 47 municipios, todos con dato (rango: ~8.400–24.900 €/pers)
- **Escala de color:** rojo (renta baja) → verde (renta alta) — **invertida** vs criminalidad
- **Granularidad:** ~1.000–2.500 hab por sección — permite ver diferencias **dentro** de cada municipio
- **Eje:** `zoom=10`, mismo centro
- **Ranking:** tabla de secciones ordenadas por renta
- ⚠️ Disclaimer explícito: renta ≠ criminalidad, es proxy socioeconómico

**Toggle:** `st.radio` horizontal sin label. Si solo existe un asset, muestra
directamente la vista disponible.

---

## 6. KPIs del header (siempre visibles)

| KPI | Descripción |
|---|---|
| Total listings | Nº de listings en el fichero del día activo |
| Nuevos hoy | Con `first_seen == today` |
| Score medio | Media de listings con m² fiable (excluye `datos_insuficientes`) |
| Precio medio | Media de todos los listings |
| Bajadas | Listings con `price_drop > 0` |
| Sin valorar | Listings con `datos_insuficientes = True` |

---

## 7. Paleta de diseño y componentes

### Colores semánticos (constantes globales)

```python
ACCENT  = "#6366f1"   # indigo-500 — acento único (gráficos, botones)
INK     = "#e4e4e7"   # zinc-200 — texto principal
MUTED   = "#a1a1aa"   # zinc-400 — texto secundario
SUBTLE  = "#52525b"   # zinc-600
BORDER  = "#27272a"   # zinc-800
SURFACE = "#18181b"   # zinc-900 — tarjetas
GRID    = "#1f1f23"   # rejilla apenas perceptible
```

### Escala de scores → color

```
≥70  #22c55e (verde)
≥50  #84cc16
≥35  #eab308 (amarillo)
≥20  #f97316 (naranja)
≥0   #ef4444 (rojo)
```

### Tipografías (Google Fonts)

- **Fraunces** (serif) — títulos y números grandes
- **Inter** (sans) — texto general
- **JetBrains Mono** — valores numéricos tabulares

### Componentes reutilizables

- `icon(name, size, color)` — SVG Lucide inline. Íconos disponibles: `layers`,
  `sparkles`, `star`, `wallet`, `trending-down`, `waves`, `map-pin`, `building`,
  `calendar`, `zap`, `ruler`, `bed`, `bath`
- `score_color(score)` — color hex para un score dado
- `style_fig(fig, title)` — aplica template oscuro a figuras Plotly
- `_bloque(titulo, subtitulo, items)` — card de scoring (Tab 6)
- `breakdown_score_details(prop)` — descompone `score_details[]` en items
- `_render_breakdown_html(items, score_final)` — HTML del desglose expandible
- `clean(text)` — quita emojis y espacios de strings de anuncios
- `zona(*textos)` — clasifica un listing en "Madrid Sur" / "Toledo Norte" / "—"
- `tipo_vivienda(*textos)` — detecta "Obra nueva" vs "Segunda mano"

---

## 8. Flujo de datos en app.py

```
cargar_datos()          → df principal (carga todos los JSON de datos/)
cargar_geojson_municipios()  → dict GeoJSON (municipios_zona.geojson)
cargar_criminalidad()        → DataFrame (criminalidad.csv)
cargar_secciones_renta()     → (dict GeoJSON, DataFrame) (secciones_renta.geojson)
calc_hipoteca()              → dict con cuota, ahorro, intereses, etc.
```

Todos los loaders son `@st.cache_data` invalidados por `mtime` del fichero.

---

## 9. Modelo de datos de un listing (JSON)

```jsonc
{
  "title": "Piso en Getafe",
  "price": 189000,
  "score": 62,
  "score_details": ["💎 Valor vs zona (+20)", "🚗 (+12)", ...],
  "location": "Sector III (Getafe)",
  "municipio": "getafe",
  "m2": 95,
  "rooms": 3,
  "bathrooms": 1,
  "floor": "3",
  "year_built": "2002",
  "energy_rating": "D",
  "features": ["Garaje", "Ascensor"],
  "source": "pisos.com",            // "pisos.com" | "idealista"
  "url": "https://...",
  "eur_m2": 1989.0,
  "first_seen": "2026-06-20",
  "last_seen": "2026-06-23",
  "price_drop": 5000,               // opcional: bajada detectada
  "previous_price": 194000,         // opcional
  "datos_insuficientes": false      // true si no hay m² fiable
}
```

---

## 10. Patrones a respetar al añadir funcionalidades

1. **Carga de datos:** añadir un `@st.cache_data` loader junto a los existentes
   (`app.py:~570`). Invalidar siempre por `mtime` del fichero de origen.

2. **Nueva pestaña:** añadir al `st.tabs([...])` en `app.py:~1034`. El orden
   importa — reflejarlo en Tab 6 "Cómo funciona".

3. **Nuevos assets:** generarlos en `scripts/build_mapa_assets.py` (ya existente).
   Documentarlos en el docstring del módulo. Datos de terceros → verificar licencia
   (CC-BY preferido; los 3 assets actuales son CC-BY-4.0).

4. **Filtros:** seguir el patrón combinativo de Tab 1: filtros anteriores reducen
   el pool de opciones de filtros posteriores.

5. **Navegación cross-tab:** usar `sessionStorage._sw_tab` + query params para
   pre-cargar estado en otra pestaña desde un botón. Ver wiring JS en `app.py:~979`.

6. **Diseño:** dark mode siempre (`SURFACE` como fondo de tarjetas). No añadir
   colores fuera de la paleta semántica. Acento = ACCENT (#6366f1). Reutilizar
   `icon()` para iconografía en vez de emojis en UI.

7. **HTML inline:** solo para casos donde Streamlit nativo no da el nivel visual
   requerido (tablas ordenables, cards compuestos). No usar `unsafe_allow_html`
   para texto simple.

8. **Mapa de seguridad:** ante nuevas capas de datos geoespaciales, añadir como
   vista adicional en el toggle de Tab 7 siguiendo el patrón `_modo_*`. La clave
   de join siempre va en `properties` del GeoJSON y en una columna del DataFrame.

9. **Fiscalidad / tipos:** los tipos ITP/AJD/IVA están hardcodeados en constantes
   al inicio de `app.py` (`ITP`, `AJD`, `IVA_OBRA_NUEVA`). Actualizarlos ahí, no
   dispersarlos.

10. **Sin dependencias nuevas** salvo justificación explícita. Stack actual:
    `streamlit`, `pandas`, `plotly`, `requests`, `json`, `pathlib`, stdlib Python.

---

## 11. Comandos operativos

```bash
# Lanzar dashboard
streamlit run dashboard/app.py

# Regenerar assets del mapa (geometrías + criminalidad + renta)
cd house-dashboard/dashboard
python scripts/build_mapa_assets.py

# Guardar una pasada del scraper
python dashboard/guardar.py ~/AppData/Local/hermes/last_property_data.json
# o por stdin
cat resultados.json | python dashboard/guardar.py --stdin
```

---

*Última actualización: 2026-06-23 — refleja commit `792282f` (capa renta secciones censales)*
