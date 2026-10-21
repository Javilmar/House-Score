# Inventario del dashboard de Streamlit (fuente de la paridad)

Generado el 2026-10-21 leyendo `frontend/dashboard/app.py` (2724 líneas) y `api_datos.py` por tramos. Las citas `app.py:LÍNEA` se refieren al commit `b6c7fd7`.

Orden visual de las pestañas (`app.py:1121`): Listados completos (`tab1`), Top scoring (`tab2`), Novedades (`tab5`), Evolución y análisis (`tab3`), Bajadas de precio (`tab4`), Hipoteca (`tab6`), Cómo funciona (`tab7`), Mapas (`tab8`). Los nombres de variable no siguen el orden visual.

## Discrepancias conocidas (no se replican)

- **Botón € Hipoteca abre la pestaña equivocada**: `goToHipoteca` y los botones `.hip-btn` guardan `_sw_tab='4'` (`app.py:1104`) y `_py_nav_tab = 4` (`app.py:1059`); el script hace clic en la pestaña de índice 4 (base 0) = *Bajadas de precio*. Hipoteca es el índice 5. El front nuevo navega a Hipoteca (Historia 5, escenario 2).
- `cod_ine` es numérico en `criminalidad.csv` y texto en `municipios_zona.geojson`: el join debe normalizar el tipo (ver §Mapas).


---

## Inventario app.py 1-560 (slice Base)

NOTA: `score_color` (app.py:607), `style_fig` (617), `parse_score_details` (642), `breakdown_score_details` (688), `_render_breakdown_html` (762), `calc_impuestos` (791), `calc_hipoteca` (824), `_render_hipoteca_inline_html` (880), `cargar_criminalidad` (574), `cargar_secciones_renta` (588), `cargar_geojson_municipios` (565) están FUERA de 1-560 (otro slice). Solo se documenta lo leído.

## 1. Imports / config (app.py:8-30)
- Imports: re, json, math, base64, unicodedata, pandas as pd, plotly.express as px, plotly.graph_objects as go, streamlit as st, streamlit.components.v1 as components, Path, date, datetime, `import api_datos` (L8-21).
- Docstring L1-6: "Dashboard de Búsqueda de Vivienda — Madrid Sur + Toledo Norte"; "Hecho a medida del scorer (pisos.com + idealista); lee los datos de la API del backend".
- `st.set_page_config(page_title="House Score", page_icon=None, layout="wide", initial_sidebar_state="collapsed")` (L23-28).
- `ASSETS_DIR = Path(__file__).resolve().parent / "assets"` (L30).

## 2. Constantes
Paleta (L34-40): ACCENT `#6366f1`; INK `#e4e4e7`; MUTED `#a1a1aa`; SUBTLE `#52525b`; BORDER `#27272a`; SURFACE `#18181b`; GRID `#1f1f23`.
SCORE_SCALE (L43-49), orden descendente de umbral (score>=umbral → color): `(70,"#22c55e"), (50,"#84cc16"), (35,"#eab308"), (20,"#f97316"), (0,"#ef4444")`.
SERIES (L52): `["#6366f1","#94a3b8","#22d3ee","#a78bfa","#2dd4bf","#94a3b8"]`.
Fiscalidad (L54-63; comentario: segunda mano → ITP autonómico; obra nueva → IVA 10% + AJD autonómico; bonificaciones no reflejadas):
- `IVA_OBRA_NUEVA = 0.10` (L57)
- `ITP = {"Comunidad de Madrid": 0.06, "Castilla-La Mancha": 0.09}` (L58)
- `AJD = {"Comunidad de Madrid": 0.0075, "Castilla-La Mancha": 0.015}` (L59)
- `OTROS_GASTOS_PCT = 0.015` notaría+registro+gestoría (L60)
- `TASACION_EUR = 400` (L61)
- `CCAA_DEFAULT = "Comunidad de Madrid"` (L62)
- `HIP_DEFAULTS = {"entrada_pct": 0.20, "plazo": 30, "tin": 0.03}` (L63)
Zonas (L351-380), listas en minúsculas SIN acentos:
- `_MADRID_SUR` (L351-370): getafe, leganes, mostoles, alcorcon, fuenlabrada, parla, pinto, valdemoro, ciempozuelos, humanes, grinon, navalcarnero, "torrejon de la calzada", "cubas de la sagra", batres, "serranillos del valle", "moraleja de enmedio", arroyomolinos (18).
- `_TOLEDO_NORTE` (L371-380): illescas, senorio (Illescas/El Señorío), sesena, quinon (Seseña/El Quiñón), yeles, ugena, esquivias. Comentario: solo los 5 municipios de interés Illescas, Seseña, Yeles, Ugena, Esquivias.
`_OBRA_NUEVA_KW` (L407-418): "obra nueva","a estrenar","nueva construccion","primera ocupacion","de obra nueva","promocion de obra","llave en mano","recien construid","vivienda nueva","promocion nueva".
`_EMOJI_RE` (L333-337): `re.compile("[\U0001f000-\U0001faff\U00002600-\U000027bf\U0001f1e6-\U0001f1ff\U00002190-\U000021ff\U00002b00-\U00002bff<VS16 U+FE0F><ZWJ U+200D>]", re.UNICODE)` (los dos últimos caracteres literales son variation selector y zero-width joiner).

## 3. Iconos (L66-92)
Lucide inline SVG, viewBox 0 0 24 24. `_ICON_PATHS` (L68-82) nombres → path data (L en app.py): layers 69 (3 paths: rombo superior + 2 chevrons), sparkles 70, star 71, wallet 72 (2 paths), trending-down 73 (`M16 17h6v-6` + `m22 17-8.5-8.5-5 5L2 7`), waves 74 (3 paths ondas), map-pin 75 (path + circle cx12 cy10 r3), building 76 (7 paths), calendar 77 (2 paths+rect 18x18 x3 y4 rx2 + `M3 10h18`), zap 78, ruler 79 (5 paths), bed 80 (`M2 4v16`,`M2 8h18a2 2 0 0 1 2 2v10`,`M2 17h20`,`M6 8v9`), bath 81 (6 paths). Leer el path exacto en esas líneas al portar (12 iconos).
`icon(name, size=16, color="currentColor", stroke=1.75)` (L85): `paths=_ICON_PATHS.get(name,"")` (nombre desconocido → svg vacío); devuelve `<svg xmlns=... width=size height=size viewBox="0 0 24 24" fill="none" stroke=color stroke-width=stroke stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-2px;flex-shrink:0;">{paths}</svg>`.

## 4. CSS global `inject_styles()` (L98-328) vía `st.markdown(..., unsafe_allow_html=True)`
- Fuentes (L102): @import Google Fonts Fraunces (ital,opsz 9..144, wght 300..600; italic 300..500), Inter 300-700, JetBrains Mono 400-600. Vars (L104-108): `--font-display:'Fraunces','Times New Roman',serif`; `--font-sans:'Inter',system-ui,-apple-system,sans-serif`; `--font-mono:'JetBrains Mono',ui-monospace,monospace`.
- Body font = var(--font-sans) (L110). `@keyframes dots-drift` (L114): background-position 0 0 → -28px -28px.
- `.stApp` (L119): bg `#09090b`, `radial-gradient(circle, rgba(255,255,255,0.18) 1.5px, transparent 1.5px)`, size 28px 28px, animation dots-drift 4s linear infinite. `.block-container` (L125): padding-top 3rem, bottom 4rem, max-width 1320px.
- h1-h4 (L128): Fraunces !important, weight 400, letter-spacing -0.02em, line-height 1.15, color #fafafa; h2,h3 color #e4e4e7.
- `[data-testid="stMetric"]` (L138) glass: bg rgba(18,18,20,0.55), blur(16px), border 1px rgba(255,255,255,0.07), radius 16px, padding 1.1rem 1.25rem, shadow 0 1px 2px rgba(0,0,0,.3), transition 200ms; hover border .13, shadow 0 4px 14px rgba(0,0,0,.4). Label (L152): .78rem/500/#a1a1aa uppercase ls .04em. Value (L156): 1.6rem/600/#fafafa.
- Tabs (L161-166): tab-list gap .25rem, border-bottom 1px #27272a; tab weight 500 color #a1a1aa padding .6rem 1rem radius 8px 8px 0 0; selected color #818cf8 weight 600.
- Tarjeta listado (L169-201): `.prop-card` (glass, radius 16, padding 1.25rem 1.5rem, mb .9rem; hover border .13 shadow 0 6px 18px rgba(0,0,0,.45)); `.prop-card-row` flex gap 1.25rem align flex-start; `.prop-card-body` flex 1 min-width 0; `.prop-price` text-right nowrap; @media max-width 640px: row wrap gap .75rem, `.prop-price` flex 1 1 100%, flex wrap, gap .4rem 1rem, text-left, border-top rgba(255,255,255,.06), pt .6rem, `.prop-price > div` nowrap; `.prop-rank` #71717a 600 .9rem; `.prop-title` 600 1.02rem #fafafa no-underline, hover #818cf8; `.prop-meta` #a1a1aa .84rem mt .4rem flex wrap gap .35rem 1rem; `.meta-item` inline-flex gap .35rem; `.meta-item svg` #71717a.
- KPI (L204-228): `.kpi-grid` grid 6 cols gap .85rem mb .5rem; ≤1100px 3 cols; ≤640px 2 cols. `.kpi-card` glass radius 16 padding 1.1rem 1.2rem, hover igual. `.kpi-icon` 34x34 radius 10 bg rgba(99,102,241,.12) color #818cf8 mb .7rem. `.kpi-label` .72rem 500 #a1a1aa uppercase ls .05em. `.kpi-value` Fraunces 1.7rem 600 #fafafa mt .1rem ls -.01em.
- Score (L230-239): `.score-badge` inline-flex centrado min-width 48px height 48px radius 12 weight 700 1.2rem color #09090b (fondo = score_color); `.score-bar-track` w100% h5px #27272a radius 999 mt .5rem; `.score-bar-fill` h100% radius 999.
- Chips (L241-246): `.chip` inline-block padding .2rem .65rem, bg #27272a, border #3f3f46, radius 999, .78rem, #d4d4d8, 500; `.chip-warn` bg #2a1215 border #5b1d22 color #fca5a5.
- `.prop-action-btn` (L247-253): bg rgba(99,102,241,.08) border rgba(99,102,241,.2) color #818cf8 radius 6 padding .28rem .75rem .82rem/500 mt .75rem inline-block; hover bg .22 border #818cf8 color #a5b4fc.
- Desglose `.score-breakdown` (L256-271): mt .85rem border-top #27272a pt .65rem; `> summary` pointer .78rem #71717a 500 list-style revert; hover #a1a1aa. `.sb-table` w100% collapse mt .55rem; `.sb-row td` padding .18rem .3rem .78rem #d4d4d8 top; `td:last-child` right nowrap JetBrains Mono min-width 3.5rem; `.sb-pts-pos` #4ade80 600; `.sb-pts-neg` #f87171 600; `.sb-pts-zero` #52525b 500; `.sb-total td` pt .4rem border-top #3f3f46 700 #fafafa .82rem; `.sb-total td:last-child` mono.
- Botones (L274-279): `.stButton button,.stDownloadButton button` radius 10 border #27272a 500 bg #18181b color #e4e4e7; `.stDownloadButton button:hover` border #6366f1 color #818cf8. `hr` border #27272a !important (L282).
- Tabla listados (L285-322): `.list-table-wrap` border #27272a radius 14 overflow hidden bg #131316; `.list-table` w100% .86rem; thead th left .7rem 600 #71717a uppercase ls .04em padding .7rem .85rem border-bottom #27272a bg #18181b nowrap; tbody td padding .65rem .85rem border-bottom #1f1f23 #d4d4d8 middle; last row sin borde; tr hover bg #18181b; `.lt-pos` mono 600 #71717a .9rem; `.lt-title a` #818cf8 500 border-bottom rgba(129,140,248,.25), hover #a5b4fc; `.lt-title span` #a1a1aa; `.lt-num` mono .8rem #a1a1aa; `.lt-price` mono 600 #fafafa; `.lt-score-wrap` flex gap .55rem min-width 96px; `.lt-score-num` mono 600 w24px #e4e4e7 .82rem; `.lt-score-track` flex1 h5px #27272a min-width 50px; `.lt-score-fill` h100% radius 999.
- `#MainMenu, footer { visibility: hidden; }` (L324).

## 5. Funciones helper
- `clean(text)` (L340): si no es str lo devuelve tal cual; `_EMOJI_RE.sub("", text).strip(" ·")` (strip de espacio y "·").
- `_sin_acentos(s)` (L383): `unicodedata.normalize("NFKD", str(s))`, descarta `combining`, `.lower()`.
- `zona(*textos)` (L388): blob=_sin_acentos(" ".join(t for t in textos if t)); si algún elem de `_MADRID_SUR` es substring → "Madrid Sur" (se evalúa PRIMERO); si no, algún de `_TOLEDO_NORTE` → "Toledo Norte"; si no "—". Búsqueda por subcadena (p.ej. "pinto" matchea "pintor").
- `zona_a_ccaa(z)` (L398): "Madrid Sur"→"Comunidad de Madrid"; "Toledo Norte"→"Castilla-La Mancha"; otro→CCAA_DEFAULT.
- `tipo_vivienda(*textos)` (L421): mismo blob; algún `_OBRA_NUEVA_KW` substring → "Obra nueva" else "Segunda mano".
- `cargar_datos()` (L553, `@st.cache_data(ttl=30)`): `api_datos.obtener_listings()`; doc: activos y retirados; si falla lanza ApiNoDisponible.
- `cargar_historico()` (L559, `@st.cache_data(ttl=30)`): `api_datos.obtener_historico()`; histórico diario.
- (L565+ fuera de rango) cargar_geojson_municipios(mtime): lee `ASSETS_DIR/"municipios_zona.geojson"`, None si no existe.

## 6. `_TABLA_TEMPLATE` (L432-546) — HTML autónomo para `components.html`
- Inyección: marcadores `__THEAD__` y `__ROWS__` (L488) sustituidos con `.replace` (comentario L429-431: no f-string). Estructura: `<div class="wrap"><table id="lt"><thead>__THEAD__</thead><tbody>__ROWS__</tbody></table></div>`.
- Página: bg #09090b, Inter; `.wrap` border #27272a radius 14 overflow auto max-height `calc(100vh - 4px)` bg #131316; table min-width 100% .86rem.
- thead th: sticky top:0 z-index 1, cursor pointer, user-select none, color #a1a1aa (aquí, no #71717a), uppercase .7rem; `th.noord` cursor default width 34px (columna de acción, no ordenable); hover (no noord) #fafafa; `.arr` #818cf8 .78rem (flecha). tbody td vertical-align top (L476, sobrescribe middle), padding .6rem .85rem.
- Clases de celda: `.lt-pos` (mono .95rem nowrap), `.lt-title a/span`, `.lt-num`, `.lt-price`, `.lt-score-wrap/num/track/fill` (como en CSS global), `.lt-tag` (.72rem padding .12rem .5rem radius 5 nowrap 500), `.lt-nuevo` (bg rgba(34,197,94,.12) #4ade80 border rgba(34,197,94,.2)), `.lt-usada` (bg rgba(255,255,255,.04) #a1a1aa border #27272a), `.lt-src` base (#94a3b8), `.lt-src-pisos` (bg rgba(234,179,8,.1) #fbbf24 border rgba(234,179,8,.2)), `.lt-src-fotocasa` (rgba(56,189,248,.1) #7dd3fc border rgba(56,189,248,.25)), `.lt-src-idealista` (rgba(99,102,241,.1) #818cf8 border rgba(99,102,241,.2)); scrollbar 8px thumb #3f3f46 radius 4; `.lt-goto-btn` (mismo estilo que prop-action-btn, padding .22rem .45rem .8rem line-height 1).
- Desglose en tabla (L477-486): `.score-breakdown` mt .45rem, summary .7rem #52525b; `.sb-table` min-width 170px mt .35rem; `.sb-row td` .7rem #a1a1aa padding .1rem .2rem; `.sb-total td` .72rem 600 #e4e4e7 border-top #27272a; `.sb-pts-pos #4ade80`, `-neg #f87171`, `-zero #52525b`, `-neu #a1a1aa` (nuevo; todos mono).
- JS `ord(idx, th)` (L522-545), llamado desde `th` (onclick generado por otro slice): rows=filas del tbody; `asc = th.getAttribute('data-dir') !== 'asc'` (primer clic = asc; alterna); limpia `data-dir` y texto de `.arr` de todos los th; comparador usa `cells[idx].getAttribute('data-v')`: `parseFloat`; ambos numéricos (x!=='' && !=null && !isNaN) → `nx-ny`; solo x numérico → -1 (números primero); solo y → 1; ninguno → `(''+x).localeCompare(''+y,'es',{sensitivity:'base'})`; `asc?c:-c`. Reinserta filas con appendChild; `th data-dir = asc|desc`; `.arr` textContent `' ▲'` asc / `' ▼'` desc. Nota: en desc los no-numéricos/vacíos quedan antes (c invertido).
- JS `goToHipoteca(precio, tipo_idx, ccaa_idx)` (L490-505): tipos=["Segunda mano","Obra nueva"], ccaas=["Comunidad de Madrid","Castilla-La Mancha"]; construye `p.location.pathname + '?hip_precio='+precio+'&hip_tipo='+encodeURIComponent(tipos[tipo_idx])+'&hip_ccaa='+encodeURIComponent(ccaas[ccaa_idx])+'&hip_nav_id='+Date.now()`; `sessionStorage.setItem('_sw_tab','4')` (pestaña índice 4 = Hipoteca); navega inyectando `<script>window.location.href=...` en el body del parent (recarga completa). Query params: hip_precio, hip_tipo, hip_ccaa, hip_nav_id.
- JS `goToCard(rank)` (L506-521): clic en `tabs[1]` de `[data-baseweb="tab"]` del parent (pestaña índice 1 = tarjetas/Top); tras 280ms reintenta (máx 12 intentos, cada 150ms) hasta encontrar `#card-<rank>`; entonces `scrollIntoView({behavior:'smooth',block:'start'})`, `boxShadow='0 0 0 2px #818cf8'` con transition 300ms, se quita a los 1800ms.
- No usa postMessage; acceso directo a `window.parent` (iframe mismo origen).

## 7. Mapa de índices de pestañas (inferido del JS)
Índice 1 = vista de tarjetas (goToCard), índice 4 = Hipoteca (goToHipoteca/_sw_tab).

---

## Inventario: api_datos.py (1-162) + app.py 540-1120

## A. api_datos.py
- L7-11 imports: `copy`, `os`, `pandas as pd`, `requests`.
- L15 `API_URL_DEFECTO = "http://127.0.0.1:8000"` (127.0.0.1 y no localhost: en Windows localhost prueba ::1 y pierde ~2 s; API solo IPv4).
- L16 `_TIMEOUT = (3, 15)` → conexión 3 s, lectura 15 s. Una sola petición, sin reintentos (L132).
- L19-34 `_PRINCIPALES` (campo API → columna app), COMPLETO:
  titulo→title, precio→price, m2→m2, habitaciones→rooms, banos→bathrooms, url→url, fuente→source, municipio→municipio, score→score, datos_insuficientes→datos_insuficientes, primera_aparicion→first_seen, ultima_aparicion→last_seen, bajada_precio→price_drop, precio_anterior→previous_price.
- L35 `_ESTADOS = {"activo": "active", "retirado": "delisted"}`; columna `status` = `_ESTADOS.get(item.get("estado"), item.get("estado"))` (valor desconocido se mantiene tal cual) (L112).
- L40-53 `_DEFECTOS_DETALLE` (se aplica si `fila.get(clave) is None`, con `copy.deepcopy`): location "", description "", floor "", conservation "", energy_rating "", pisos_id "", features [], detail_features {}, score_details [], exterior False, cumple_requisitos True, year_built 0.
- Mapping de detalle: NO hay tabla de renombrado; `fila = dict(item.get("detalle") or {})` → TODAS las claves del objeto `detalle` pasan tal cual como columnas (nombres ya = columnas de app.py). `eur_m2` del detalle se descarta (`fila.pop("eur_m2", None)`) y se recalcula. Las claves principales se escriben DESPUÉS → una clave del detalle nunca pisa una principal. Si falta una clave principal en el item → `None`.
- L59 `_CERO_SI_FALTA = ["price","m2","rooms","bathrooms","score"]` → `df[col].fillna(0)` (se aplica sin comprobar existencia de columna; tras to_numeric).
- L60 `_NUMERICAS = ["price","m2","rooms","bathrooms","score","year_built","price_drop","previous_price"]` → `pd.to_numeric(errors="coerce")` solo si la columna existe.
- L62-68 `_HISTORICO`: total_listings→count, score_medio→avg_score, precio_medio→avg_price, precio_min→min_price, precio_max→max_price.
- L71-77 `class ApiNoDisponible(Exception)`: `__init__(self, mensaje, url)`; `super().__init__(f"{mensaje} ({url})")`; atributos `.mensaje`, `.url`.
- L80-85 `url_api(api_url=None)`: `(api_url or os.environ.get("HOUSESCORE_API_URL") or API_URL_DEFECTO).rstrip("/")`. Se lee en cada llamada.
- L88-115 `listings_a_dataframe(items)`: `if not items: return pd.DataFrame()` (vacío). Por item: dict(detalle) → pop eur_m2 → defectos → principales → status. Luego DataFrame; to_numeric de _NUMERICAS; fillna(0) de _CERO_SI_FALTA; `first_seen`/`last_seen` = `pd.to_datetime(errors="coerce")` (L109-110); **`eur_m2 = (df["price"] / df["m2"].where(df["m2"] > 0)).round(0)`** (m²=0 → NaN) (L113); retorna `df.sort_values("score", ascending=False, na_position="last")` (L115). Índice NO se resetea.
- L118-128 `historico_a_dataframe(filas)`: vacío→`pd.DataFrame()`; `pd.DataFrame(filas).rename(columns=_HISTORICO)`; `fecha = pd.to_datetime(errors="coerce")`; to_numeric(coerce) de las 5 columnas de `_HISTORICO.values()` si existen; `sort_values("fecha")`.
- L131-154 `_pedir(ruta, api_url, params=None)`: `url = f"{url_api(api_url)}{ruta}"`; `requests.get(url, params=params, timeout=_TIMEOUT)`. Errores (todos `ApiNoDisponible(mensaje, url)`):
  - `requests.exceptions.Timeout` → "La API no ha respondido a tiempo"
  - otro `RequestException` → "No se puede conectar con la API"
  - status 429 → "La API ha limitado las peticiones; espera un momento y recarga"
  - status != 200 → f"La API ha devuelto un error (HTTP {respuesta.status_code})"
  - `respuesta.json()` ValueError → "La respuesta de la API no es válida"
  - JSON no es lista, o algún elemento no es dict → "La respuesta de la API no es válida"
  - (Orden: Timeout se captura antes que RequestException.)
- L157-158 `obtener_listings(api_url=None)`: GET `/listings` con params `{"incluir_retirados": "true"}`.
- L161-162 `obtener_historico(api_url=None)`: GET `/historico` sin params.
- Sin auth, sin cabeceras, sin paginación.

## B. app.py 540-1120

### Constantes referenciadas (fuera del rango, para tests)
- L30 `ASSETS_DIR = Path(__file__).resolve().parent / "assets"`.
- Paleta L34-40: ACCENT "#6366f1", INK "#e4e4e7", MUTED "#a1a1aa", SUBTLE "#52525b", BORDER "#27272a", SURFACE "#18181b", GRID "#1f1f23".
- L43-49 `SCORE_SCALE = [(70,"#22c55e"),(50,"#84cc16"),(35,"#eab308"),(20,"#f97316"),(0,"#ef4444")]`; L52 `SERIES = ["#6366f1","#94a3b8","#22d3ee","#a78bfa","#2dd4bf","#94a3b8"]`.
- L57-63: `IVA_OBRA_NUEVA = 0.10`; `ITP = {"Comunidad de Madrid": 0.06, "Castilla-La Mancha": 0.09}`; `AJD = {"Comunidad de Madrid": 0.0075, "Castilla-La Mancha": 0.015}`; `OTROS_GASTOS_PCT = 0.015`; `TASACION_EUR = 400`; `CCAA_DEFAULT = "Comunidad de Madrid"`; `HIP_DEFAULTS = {"entrada_pct": 0.20, "plazo": 30, "tin": 0.03}`.
- L340-344 `clean(text)`: no-str → devuelve tal cual; `_EMOJI_RE.sub("", text).strip(" ·")`.
- L432 `_TABLA_TEMPLATE` (otro slice); L540-546 es el final del JS del template de tabla (sort: `asc ? c : -c`, reordena `rows` en `tb`, `th.setAttribute('data-dir', asc?'asc':'desc')`, flecha `.arr` textContent `' ▲'`/`' ▼'`; cierra `</script></body></html>"""`).

### Cargadores y caché (L549-604)
- L552 `@st.cache_data(ttl=30)` `cargar_datos()` → `api_datos.obtener_listings()`. Lanza ApiNoDisponible (la excepción no se cachea).
- L558 `@st.cache_data(ttl=30)` `cargar_historico()` → `api_datos.obtener_historico()`.
- L564 `@st.cache_data` (sin TTL) `cargar_geojson_municipios(mtime: float = 0.0)`: `ASSETS_DIR/"municipios_zona.geojson"`; no existe → `None`; si no, `json.loads(read_text(encoding="utf-8"))`. mtime solo es clave de caché.
- L573 `@st.cache_data` `cargar_criminalidad(mtime=0.0)`: `ASSETS_DIR/"criminalidad.csv"`; no existe → `pd.DataFrame()`; `pd.read_csv(path, comment="#")`; `df_c["tasa_criminalidad"] = pd.to_numeric(errors="coerce")`. Columnas CSV usadas aquí: `tasa_criminalidad` (resto en otros slices).
- L587 `@st.cache_data` `cargar_secciones_renta(mtime=0.0)`: `ASSETS_DIR/"secciones_renta.geojson"`; no existe → `(None, pd.DataFrame())`; carga gj; `rows = [feat["properties"] for feat in gj.get("features", [])]`; sin rows → `(gj, pd.DataFrame())`; `df_r = pd.DataFrame(rows)`; `renta_persona` to_numeric coerce; devuelve `(gj, df_r)`. Docstring: columnas cusec, cod_ine, municipio, renta_persona, anio (ADRH 2023 INE).
- Nota: no hay loader de histórico CSV/JSON local; todo viene de la API. Las columnas derivadas zona/tipo/novedades/dias en mercado NO se calculan en 540-1120 (aparecen tras L1120; pertenecen a otro slice). En este rango el único derivado del df es `eur_m2`(api_datos L113), `status`, `first_seen/last_seen`.

### Helpers (L607-636)
- L607-611 `score_color(score)`: itera SCORE_SCALE, primer `score >= threshold` → color; si ninguno → `SCORE_SCALE[-1][1]` ("#ef4444").
- L617-636 `style_fig(fig, title=None)` layout Plotly: title=`dict(text=title, font=dict(size=16,color=INK,family="Fraunces"))` si title, si no None; font `Inter` size 12 color MUTED; paper_bgcolor/plot_bgcolor `"rgba(0,0,0,0)"`; margin `l=12,r=12,t=44 si title else 12,b=12`; height=350; legend bgcolor transparente, font size 11; hoverlabel bgcolor SURFACE, bordercolor BORDER, font Inter color INK. xaxes: showgrid False, zeroline False, linecolor BORDER, tickcolor BORDER. yaxes: showgrid True, gridcolor GRID, zeroline False, linecolor "rgba(0,0,0,0)".

### Score details
- L642-670 `parse_score_details(prop)` → `(features, penalties, bonuses)`, cada elemento pasa por `clean(d)`. `details = prop.get("score_details", [])`. Reglas en orden elif:
  1. penalties: `"⚠️" in d or "🕸️" in d or "❓" in d`
  2. features: cualquier de `["🏊","🚗","📦","🌿","🏡","🛗","🌳","🏗️","🔧","🚇","🏢","⚡","📅"]` en d
  3. bonuses: `"💰" in d or "📐" in d or "💎" in d or "📉" in d`
  4. otro: ignorado. (nótese: 📐/💎 no se ven por la regla 2 salvo que contenga otro emoji.)
- L674-682 `FEATURE_NAMES`: 🏊 Piscina, 🚗 Garaje, 📦 Trastero, 🌿 Terraza, 🏡 Patio, 🛗 Ascensor, 🌳 Jardín.
- L684 `_PTS_RE = re.compile(r"\s*\(([+-]?\d+)\s*(?:pts)?\)\s*$")`
- L685 `_CAP_RE = re.compile(r"características capadas:\s*(\d+)[→>](\d+)", re.IGNORECASE)`
- L688-759 `breakdown_score_details(prop)` → `(items, score_final)`:
  - `score_final = int(prop.get("score", 0) or 0)`; `details = prop.get("score_details", [])`.
  - Elementos no-str: se saltan (L695).
  - Si `_CAP_RE.search(d)` (L699): raw=g1, capped=g2; item `{"label": f"Características (tope: {raw}→{capped})", "points": capped - raw, "categoria": "características"}`; `continue`.
  - Si `_PTS_RE.search(d)`: `pts=int(g1)`, `label_raw = _PTS_RE.sub("", d).strip()`; si no: `pts=0`, `label_raw=d.strip()`.
  - Expansión (L722): si `label_raw.rstrip() == emoji` para algún FEATURE_NAMES → `f"{emoji} {name}"`.
  - Categoría (sobre `d` original, orden elif): 💎 o ❓ → "valor"; 📐 → "tamaño"; cualquiera de 🏊🚗📦🌿🏡🛗🌳 → "características"; cualquiera de 🏗️🔧📅 → "estado"; cualquiera de 🚇🏢⚡ → "ubicación"; 📉 o 💰 → "mercado"; ⚠️ o 🕸️ → "penalización"; resto → "otro".
  - Label conserva emoji (no se hace clean).
  - Reconciliación (L748-757): `suma = sum(points)`; si `suma != score_final`: añade `{"label": "Ajuste (límite 0-100)", "points": score_final - suma, "categoria": "penalización" if ajuste < 0 else "otro"}`.
- L762-785 `_render_breakdown_html(items, score_final)`: por item `<tr class="sb-row"><td>{label}</td><td>{pts_html}</td></tr>`; pts>0 → `<span class="sb-pts-pos">+{pts}</span>`; pts<0 → `<span class="sb-pts-neg">{pts}</span>`; 0 → `<span class="sb-pts-zero">0</span>`. Envoltorio: `<details class="score-breakdown"><summary>Ver desglose de puntuación</summary><table class="sb-table">{filas}<tr class="sb-total"><td>Total</td><td>{score_final}</td></tr></table></details>`. Label sin escapar HTML.

### Hipoteca (L791-924)
- L791-821 `calc_impuestos(precio, es_obra_nueva, ccaa)` → `{"items": [(etiqueta, importe)...], "total": int}`.
  - `p=float(precio)`; si no `p>0 and isfinite(p)` o TypeError/ValueError → `{"items": [], "total": 0}`.
  - Obra nueva: `iva=round(p*0.10)`; `ajd_tipo=AJD.get(ccaa, AJD[CCAA_DEFAULT])`; `ajd=round(p*ajd_tipo)`; items `[("IVA (10%)", iva), (f"AJD ({ajd_tipo*100:.2f}% — {ccaa})", ajd)]`; total=iva+ajd.
  - Segunda mano: `itp_tipo=ITP.get(ccaa, ITP[CCAA_DEFAULT])`; `itp=round(p*itp_tipo)`; items `[(f"ITP ({itp_tipo*100:.0f}% — {ccaa})", itp)]`; total=itp. (ccaa desconocida → tipo de Madrid pero etiqueta con el nombre dado.) `round` = Python (bancario, half-to-even).
- L824-877 `calc_hipoteca(precio, entrada_pct, plazo_anios, tin, es_obra_nueva, ccaa)`:
  - precio inválido (no float, ≤0, no finito) → dict todo 0: principal, entrada, cuota_mensual, impuestos `{"items": [], "total": 0}`, otros_gastos, ahorro_necesario, total_intereses, total_pagado.
  - `entrada=round(p*entrada_pct)`; `principal=round(p-entrada)`; `n=int(plazo_anios)*12`; `r=tin/12`.
  - `if r>0 and n>0: cuota = principal*r/(1-(1+r)**(-n))`; `elif n>0: cuota = principal/n`; `else: cuota=0`.
  - `total_pagado_prestamo = cuota*n`; `total_intereses = max(0, total_pagado_prestamo - principal)`.
  - `impuestos = calc_impuestos(p, es_obra_nueva, ccaa)`; `otros_gastos = round(p*0.015) + 400`; `ahorro_necesario = entrada + impuestos["total"] + otros_gastos`.
  - Devuelve: principal, entrada, `cuota_mensual=round(cuota)`, impuestos, otros_gastos, ahorro_necesario, `total_intereses=round(total_intereses)`, `total_pagado=round(total_pagado_prestamo + entrada + impuestos["total"] + otros_gastos)`.
- L880-924 `_render_hipoteca_inline_html(precio, es_obra_nueva, ccaa)`: calcula con HIP_DEFAULTS (0.20, 30, 0.03). `cuota_mensual == 0` → `""`. `_e(v)` = `f"{int(round(v)):,}".replace(",", ".") + " €"`. `tipo_str` ("Obra nueva"/"2ª mano") se calcula pero NO se usa. summary: `hipoteca ~{_e(cuota)}/mes <span style='color:#52525b;font-size:0.68rem;'>(80%, {plazo} a., {tin*100:.1f}%)</span>` → "(80%, 30 a., 3.0%)". Filas (class `sb-row`, valores `td.sb-pts-neu`): "Entrada (20%)"; una por impuesto (etiqueta, `_e(importe)`); "Otros gastos (gestoría, notaría, tasación…)"; `<tr class="sb-total"><td>Ahorro necesario</td><td>{_e(ahorro_necesario)}</td></tr>`; fila con estilo `color:#52525b;` "Total pagado (préstamo + entrada + gastos)". Envuelto en `<details class="score-breakdown"><summary>…</summary><table class="sb-table">…</table></details>`.

### UI (L927-1117)
- L929 `inject_styles()`.
- L932-960 `components.html(<script>, height=0)` botón volver arriba: usa `window.parent`; si ya existe `#_back-top` en parent doc → return. Crea `button#_back-top`, texto `'↑'`, title `'Volver arriba'`, estilo: position fixed, bottom 1.5rem, right 1.5rem, z-index 9999, 40x40px, border-radius 50%, background rgba(99,102,241,0.15), border 1px solid rgba(99,102,241,0.35), color #818cf8, font-size 1.1rem, cursor pointer, display none, align-items/justify-content center, transition `opacity 200ms ease,background 140ms ease`, backdrop-filter blur(8px) (+webkit). Click → `p.scrollTo({top:0,behavior:'smooth'})`; mouseenter bg rgba(99,102,241,0.3), mouseleave rgba(99,102,241,0.15). Scroll listener (passive): `display = p.scrollY > 300 ? 'flex' : 'none'`.
- L962 `st.title("House Score")`.
- L963-965 `st.caption("Madrid Sur · Toledo Norte — pisos.com · idealista · Scoring a medida · Hasta 300.000 €")`.
- L967-975 `df = cargar_datos()`; en `ApiNoDisponible as e`: `st.error(f"**{e.mensaje}.** Dirección consultada: `{e.url}`\n\nArranca la API con `cd backend && docker compose up -d` y recarga esta página.")` y `st.stop()` (sin cifras, sin datos antiguos).
- L977-983 `df.empty`: `st.warning("La API no tiene listings todavía.")`; `st.info("Ejecuta el scorer del repositorio (`backend/worker/scraper/property_scorer_all.py`): cada lote envía su pasada a la API.")`; `st.stop()`.
- KPIs (L987-1035):
  - `hoy = date.today()`.
  - `nuevos_hoy = df[df["first_seen"] == pd.Timestamp(hoy)]` si existe columna first_seen, si no DataFrame vacío.
  - `activos = df[df["status"] == "active"]` si existe `status`, si no df.
  - `bajadas = df[df["price_drop"].notna() & (df["price_drop"] > 0)]` si existe price_drop, si no vacío (cuenta sobre df completo, incluye retirados).
  - `di_mask = df["datos_insuficientes"].fillna(False).astype(bool)`; `sin_valorar = df[di_mask]`; `fiables = df[~di_mask]` (si no hay columna: sin_valorar vacío, fiables=df).
  - `score_src = fiables if ("score" in fiables.columns and not fiables.empty) else df`.
  - Lista kpis (icono, label, valor), en orden:
    1. ("layers","Total listings", `f"{len(activos)}"`)
    2. ("sparkles","Nuevos hoy", `f"{len(nuevos_hoy)}"`) (df completo, incluye retirados)
    3. ("star","Score medio", `f"{score_src['score'].mean():.1f}"` si hay columna score, si no "—")
    4. ("wallet","Precio medio", `f"{df['price'].mean():,.0f} €"` si hay price, si no "—") — media sobre df COMPLETO (activos+retirados, incluye price=0 por fillna(0)); separador de miles coma (formato Python `,`).
    5. ("trending-down","Bajadas", `f"{len(bajadas)}"`)
    6. ("ruler","Sin valorar", `f"{len(sin_valorar)}"`)
  - HTML: `<div class="kpi-grid">` con por KPI `<div class="kpi-card"><div class="kpi-icon">{icon(name, size=18)}</div><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div></div>`; `st.write("")` antes y después.
- Precarga hipoteca por query params (L1038-1053): `_hip_qp = st.query_params`; `_hip_nav_id = _hip_qp.get("hip_nav_id","")`. Si no vacío y `st.session_state.get("_last_hip_nav_id") != _hip_nav_id`: guarda `_last_hip_nav_id`; `session_state["hip_precio"] = int(_hip_qp["hip_precio"])` (ignora KeyError/TypeError/ValueError); si `hip_tipo` en qp → `session_state["hip_tipo"]` = valor; si `hip_ccaa` en qp → `session_state["hip_ccaa"]`. Query params: `hip_precio`, `hip_tipo`, `hip_ccaa`, `hip_nav_id`.
- Watcher (L1055-1081): `_py_nav_tab = 4 if st.session_state.pop("_hip_py_nav", False) else "null"` (flag lo pone el botón € de Tab 2/Tab 4; índice de pestaña destino = 4, hipoteca). `components.html(script, height=0)`: `p=window.parent`; `ss = p.sessionStorage.getItem('_sw_tab')`; `idx = ss !== null ? parseInt(ss,10) : {_py_nav_tab}`; si `ss !== null` → `removeItem('_sw_tab')`; si `idx === null || idx !== idx(NaN)` → return. `tryClick()`: `t = p.document.querySelectorAll('[data-baseweb="tab"]')`; si `t.length > idx` → `t[idx].click()`, true. Si falla: `MutationObserver` sobre `p.document.body` `{childList:true, subtree:true}` que reintenta tryClick y `disconnect()` al éxito; `setTimeout(disconnect, 4000)`.
- Wire-up botones € (L1083-1117): `components.html(script, height=0)`. `tipos = ["Segunda mano","Obra nueva"]`; `ccaas = ["Comunidad de Madrid","Castilla-La Mancha"]`. `wire()`: para cada `.hip-btn:not([data-wired])` en parent doc → `data-wired='1'`; click: lee `data-precio` (string), `data-tipo` (int idx a tipos), `data-ccaa` (int idx a ccaas); `url = p.location.pathname + '?hip_precio=' + precio + '&hip_tipo=' + encodeURIComponent(tipos[tipo]) + '&hip_ccaa=' + encodeURIComponent(ccaas[ccaa]) + '&hip_nav_id=' + Date.now()`; `p.sessionStorage.setItem('_sw_tab','4')`; inyecta `<script>` en parent body con `window.location.href=<JSON url>;` (recarga completa). `wire()` inmediato + `MutationObserver(wire)` sobre body `{childList:true, subtree:true}` (sin disconnect).
- L1119 comienza sección "Pestañas".

Total ítems documentados: ~62 (api_datos 17, app.py 45).

---

## Inventario app.py 1119-1720 (InvTabs1)

NOTA: en este rango NO está Novedades (`tab5`): su cuerpo está en ~1850-1930 (el `hip-btn` de Novedades usa `_n_*`, app.py:1924-1927). El rango contiene: definición de pestañas, iconos, tab1, tab2, tab3 completa y el inicio de tab4 (1720 corta dentro del bucle de cards de tab4; el resto lo documenta otro slice).

## 0. Contexto/datos usados (fuera del rango, solo referencia)
- `df = cargar_datos()` (app.py:553 → `api_datos.obtener_listings()`, cache ttl=30). Orden: `df.sort_values("score", ascending=False, na_position="last")` (api_datos.py:115). Por tanto "df" ya viene ordenado por score desc; el rank global y el Top N dependen de ese orden.
- `hoy = date.today()` (app.py:987). `bajadas = df[df["price_drop"].notna() & (df["price_drop"] > 0)]` si existe la columna price_drop, si no `pd.DataFrame()` (994-998).
- Helpers: `icon` 85, `clean` 340, `zona` 388, `zona_a_ccaa` 398, `tipo_vivienda` 421, `_TABLA_TEMPLATE` 432, `goToHipoteca/goToCard/ord` JS 490-~560, `cargar_historico` 559, `score_color` 607, `style_fig` 617, `parse_score_details` 642, `breakdown_score_details` 688, `_render_breakdown_html` 762. Colores: ACCENT `#6366f1` (34), SUBTLE `#52525b` (37).

## 1. Pestañas (1119-1132)
- `tab1, tab2, tab5, tab3, tab4, tab6, tab7, tab8 = st.tabs([...])` — orden visual y etiquetas exactas:
  1. "Listados completos" (tab1) 2. "Top scoring" (tab2) 3. "Novedades" (tab5) 4. "Evolución y análisis" (tab3) 5. "Bajadas de precio" (tab4) 6. "Hipoteca" (tab6) 7. "Cómo funciona" (tab7) 8. "Mapas" (tab8).
- Índice 0-based: Listados=0, Top scoring=1 (goToCard hace `tabs[1].click()`, app.py:509), Hipoteca=**4 en sessionStorage `_sw_tab`** (1104; 'Hipoteca' visual idx 5 — el watcher que lo lee está fuera del rango; verificar contra otro slice, el comentario de 497 dice "indice 4 = Hipoteca" aunque visualmente es la 6ª).

## 2. Iconos SVG en pestañas (1135-1193)
- `_tab_svg_uri(inner)`: SVG `viewBox="0 0 24 24" fill="none" stroke="#000" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"` + base64 → `data:image/svg+xml;base64,...` (1136-1143).
- `_INFO_ICON_PATH = "<circle cx='12' cy='12' r='10'/><path d='M12 16v-4'/><path d='M12 8h.01'/>"` (1146-1148).
- `_TAB_ICON_LIST` (1150-1159), orden = orden visual de pestañas (OJO: no el de variables): `_ICON_PATHS["layers"]` (Listados), `["star"]` (Top scoring), `["sparkles"]` (Novedades), `["waves"]` (Evolución y análisis), `["trending-down"]` (Bajadas), `["wallet"]` (Hipoteca), `_INFO_ICON_PATH` (Cómo funciona), `["map-pin"]` (Mapas). (Paths Lucide en `_ICON_PATHS`, app.py ~45-84, otro slice.)
- CSS por pestaña (1161-1167): `[data-baseweb='tab-list'] button[role='tab']:nth-of-type({i+1})::before { mask-image: url(uri) }`.
- CSS común (1168-1193): botón tab `display:inline-flex !important; align-items:center; gap:6px`; `::before` `content:''; width:14px; height:14px; flex-shrink:0; background-color:currentColor; mask-size:contain; mask-repeat:no-repeat; mask-position:center; opacity:0.85`.

## 3. Wire-up botones "€ Hipoteca" (cards) (1083-1117, justo antes del rango, necesario)
- Script `components.html(height=0)`; en cada `.hip-btn:not([data-wired])` pone `data-wired=1` y listener click: lee `data-precio`, `data-tipo` (int), `data-ccaa` (int). `tipos=["Segunda mano","Obra nueva"]`, `ccaas=["Comunidad de Madrid","Castilla-La Mancha"]`.
- Navega a `pathname + '?hip_precio='+precio + '&hip_tipo='+encodeURIComponent(tipos[tipo]) + '&hip_ccaa='+encodeURIComponent(ccaas[ccaa]) + '&hip_nav_id='+Date.now()` y hace `sessionStorage.setItem('_sw_tab','4')` (1104). MutationObserver sobre `body` {childList, subtree} re-ejecuta `wire` (1112-1113).
- Equivalente para la tabla: `goToHipoteca(precio,tipo_idx,ccaa_idx)` (app.py:490-505) idéntica URL/params.

## 4. TAB 1 — Listados completos (`with tab1:` 1197-1471)
### Controles
- `st.write("")` (1198).
- Checkbox **"Mostrar retirados"**, `value=False`, key `f1_retirados` (1200-1202).
- Fila 1: `st.columns(4)` (1225) → col_f1..f4.
  - col_f1 `st.multiselect("Zona", zonas_disp, default=[], key="f1_zona")` (1230). `zonas_disp = [z for z in ("Madrid Sur","Toledo Norte") if z in set(base["_zona"])]` (1227-1229) (solo las presentes en `base`, orden fijo).
  - col_f2 `st.multiselect("Municipio", municipios, default=[], key="f1_muni")` (1237). `muni_pool = base[base["_zona"].isin(filtro_zona)] if filtro_zona else base` (1233); `municipios = sorted(m for m in muni_pool["_municipio"].dropna().unique() if m and m != "—")` (1234-1236). → **Zona acota las opciones de Municipio** (filtros combinativos, comentario 1232). Nota: las opciones de municipio NO dependen de score/precio/rooms, y una selección previa de municipio no se limpia explícitamente si la zona cambia.
  - col_f3 `st.slider("Rango de score", 0, 100, (0, 100), key="f1_score")` (1239) step por defecto (1).
  - col_f4 (1240-1252): si `"price" in base.columns and base["price"].notna().any()`: `pmin,pmax = int(base["price"].min()), int(base["price"].max())`; `st.slider("Rango de precio (€)", pmin, pmax, (pmin,pmax), step=1000, format="%,d €", key="f1_precio")`; si no `filtro_precio=None`. min/max calculados sobre `base` (ya filtrada por retirados), no sobre el resultado filtrado.
- Fila 2: `st.columns([1, 3])` (1254); col_f5: si `rooms` existe y tiene algún notna: `rmin=int(min), rmax=int(max)` (de `base["rooms"].dropna()`); `st.slider("Habitaciones", rmin, rmax, (rmin,rmax), key="f1_rooms")` **solo si `rmin < rmax`**, si no `filtro_rooms=None` (1255-1265). col_f6 vacía.
### Derivación de `base` (1204-1223)
- `base = df.copy()` si `mostrar_retirados` o no hay columna `status`; si no `df[df["status"] != "delisted"].copy()` (1205-1209).
- `base["_zona"] = [zona(location, title, description) for r in records]` (1210-1214) con `r.get("location","")`, `r.get("title","")`, `r.get("description","")`.
- `_muni(r)` (1216-1221): si `municipio` es str no vacío → `m.replace("_"," ").title()`; si no regex `\(([^)]+)\)` sobre `str(location or "")` → grupo 1 `.strip()`; si no `"—"`. `base["_municipio"]`.
### Orden de aplicación de filtros (1267-1291), sobre `df_filtrado = base.copy()`
1. zona (`_zona.isin`) 2. municipio (`_municipio.isin`) 3. score (si col `score`: `>= rango[0] & <= rango[1]`) 4. precio (`if filtro_precio and "price" in cols`: `>=0 & <=1`) 5. habitaciones (`if filtro_rooms and "rooms" in cols`). Todos inclusivos, AND.
- Los filtros no usan "Mostrar retirados" después (ya aplicado en `base`).
### Ordenación inicial
- `df_tabla = df_filtrado.copy(); if "score" in cols: sort_values("score", ascending=False)` (1309-1311). Luego el usuario puede reordenar en cliente (JS `ord(idx, th)`, 490+/~528: toggle asc/desc por `data-dir`, flecha en `.arr`, compara numérico con `data-v` si parseFloat válido, texto si no).
- `url_to_rank = {str(url): i for i,(_,r) in enumerate(df.iterrows())}` — rank global en `df` completo sin filtrar (1323).
### Columnas renderizadas (thead 1451-1463) — 11 columnas
`""`(noord, medalla), `Título`(ord 1), `Precio`(2), `Score`(3), `€/m²`(4), `m²`(5), `Tipo`(6), `Fuente`(7), `Ubicación`(8), `Días`(9, title "Días en mercado"), `""`(noord, width:38px, title "Ver en Top scoring").
- Medallas: `{0:"🥇",1:"🥈",2:"🥉"}` por posición `i` en `df_tabla` (orden mostrado inicial, no rank global) (1325, 1327-1328); resto vacío. Celda `<td class="lt-pos">`.
- Título: `clean(row.title) or "Sin título"`; si `url` str que empieza por `http` → `<a href=url target="_blank" rel="noopener">`, si no `<span>` (1331-1336). `data-v=titulo.lower()`.
- Badge **s/valorar**: si `datos_insuficientes` notna y bool True → prefijo `<span class="lt-tag lt-usada" title="Sin m² fiable: no valorado">s/valorar</span> ` (1337-1342).
- Badge **retirado**: si `row.get("status")=="delisted"` → prefijo `<span class="lt-tag lt-usada" title="Sin apariciones recientes en el scraping">retirado</span> ` (1343-1347). Orden final del prefijo: `retirado` antes que `s/valorar` (retirado se antepone después).
- Precio: `_fmt_eur` (1313-1320): float finito → `f"{int(round(f)):,}".replace(",",".") + " €"`; si no `"—"`. `data-v=_num(price)` (`_num`: float finito o `""`) (1322-1325).
- Score: `sc = row.score or 0`, no finito/no numérico→0; celda `data-v="{sc:.0f}"` con `lt-score-num` `{sc:.0f}`, barra `lt-score-fill` width `min(sc,100)%` color `score_color(sc)` + `bd_html` = `_render_breakdown_html(bd_items, bd_total)` si `bd_items` (de `breakdown_score_details(row)`) (1349-1358, 1370-1375, 1428-1431).
- €/m²: `_fmt_eur(eur_m2)`, `data-v=_num(eur_m2)`. m²: `int(m2)` si notna y finito, si no `"—"` (1352-1353).
- Tipo: `tipo_vivienda(title, description, " ".join(features) si features es list)`; clase `lt-nuevo` si `"Obra nueva"` si no `lt-usada`; `<span class="lt-tag {cls}">{tipo}</span>` (1356-1363).
- Fuente: `src_raw=str(source or "").strip().lower()`; label `src_raw` o `"—"`; clase `lt-src lt-src-pisos` (contiene "pisos"), `lt-src lt-src-fotocasa` ("fotocasa"), `lt-src lt-src-idealista` ("idealista"), si no `lt-src` (1412-1421).
- Ubicación: `ubi = zona(location,title,description)` (Madrid Sur / Toledo Norte / —) (1354-1356).
- Días: `fs=first_seen`; `_dias_val=(hoy - pd.Timestamp(fs).date()).days` si notna, excepción → None; texto `"{n}d"` o `"—"`; `data-v` = n o `9999`; color `#f87171` si >45, `#fbbf24` si >20, si no `#a1a1aa` (incl. None); `white-space:nowrap` (1377-1391).
### Acciones por fila (última columna)
- `ccaa_fila = zona_a_ccaa(ubi)`; `_precio_int = int(row.get("price") or 0)`; `_tipo_idx = 1 if Obra nueva else 0`; `_ccaa_idx = 1 if ccaa == "Castilla-La Mancha" else 0` (1393-1398).
- Botón `€` (`class="lt-goto-btn"`, `onclick="goToHipoteca({precio},{tipo_idx},{ccaa_idx})"`, `title="Calcular hipoteca"`, `margin-top:0.3rem`) siempre (1399-1404).
- Botón `↗` (`onclick="goToCard({global_rank})"`, `title="Ver en Top scoring"`) solo si `0 <= global_rank < 30` (1406-1416): celda con flex column, centrado, gap 0.2rem: ↗ arriba, € debajo. Si no, solo el `€` centrado. `goToCard`: clic en `tabs[1]` (Top scoring), tras 280ms busca `#card-{rank}` (hasta 12 reintentos cada 150ms), `scrollIntoView smooth start`, `box-shadow 0 0 0 2px #818cf8` 1800ms (app.py:506-520).
  - Nota: `rank<30` coincide con el máximo del slider Top scoring (30).
### Render tabla
- Si `filas`: `doc = _TABLA_TEMPLATE.replace("__THEAD__", thead).replace("__ROWS__", "".join(filas))`; `altura = min(660, 64 + len(filas)*41)`; `components.html(doc, height=altura, scrolling=False)` (1464-1468 aprox; líneas 1451-1467).
- Vacío: `st.info("No hay listados con esos filtros.")` (1470).
- Caption: `f"{len(df_filtrado)} listings · clic en una cabecera para ordenar · clic en el título para abrir el anuncio"` (1472-1474) (cuenta sin importar si hay filas).
### CSV
- `columnas_csv` = las que existan en `df_filtrado` de, en este orden: `title, price, score, eur_m2, location, m2, rooms, bathrooms, floor, year_built, energy_rating, source, first_seen, url` (1293-1309). OJO: no incluye `_zona`, `_municipio`, status ni días.
- `csv_data = df_filtrado[columnas_csv].to_csv(index=False).encode("utf-8")` (orden = el de `df_filtrado`, que es el de `base` = score desc, no el de pantalla) ; `st.download_button("Descargar CSV", csv_data, f"listings_{hoy}.csv", "text/csv")` → nombre `listings_YYYY-MM-DD.csv` (1475-1476; línea 1471 según grep, rango real 1470-1471). Sin key.

## 5. TAB 2 — Top scoring (`with tab2:` ~1474-1595)
(Líneas: tab2 comienza tras el CSV; `top_n` slider en la primera línea tras `st.write("")`.)
- Slider `st.slider("Mostrar top", 5, 30, 15, key="tab2_slider")` (min 5, max 30, default 15, step 1).
- Fuente: `df.head(top_n)` (df completo ordenado por score desc, **incluye retirados**; sin filtros de tab1). Índice `i` 0-based; cada card `id="card-{i}"` (destino de ↗) con `style="scroll-margin-top:80px;"`.
- Por fila: `score = row.score or 0`; `features, penalties, _ = parse_score_details(row)`; `breakdown_items, _ = breakdown_score_details(row)`; `color = score_color(score)`.
- Título: `clean(title or "Sin título") or "Sin título"`; enlace `<a class="prop-title" href=url target="_blank">` si url http, si no `<span class="prop-title">`. **No hay badges retirado / s/valorar en las cards de Top scoring.**
- `meta_fields` (iconos Lucide size 15): `("map-pin", location or "—")`, `("building", f"Planta {floor or '—'}")`, `("calendar", year_built or "—")`, `("zap", energy_rating or "—")`; cada valor `clean(str(val)) or "—"`, clase `meta-item`.
- Valores: `precio=price or 0`, `eur_m2`, `m2`, `rooms`, `baths` (`or 0`).
- Chips: `features` → `<span class="chip">`; `penalties` → `<span class="chip chip-warn">` (en `<div style="margin-top:0.75rem;">`).
- Hipoteca: `_t2_ubi = zona(location,title,description)`; `_t2_tipo = tipo_vivienda(title, description, "")` (sin features, a diferencia de tab1); `_t2_tipo_idx = 1 if Obra nueva`; `_t2_ccaa_idx = 1 if zona_a_ccaa(_t2_ubi)=="Castilla-La Mancha"`.
- Descripción: `_desc_raw = description`; si `_desc_raw` y `len(_desc_raw) > 20` → `clean(_desc_raw[:1500])` (**truncado a 1500 chars**), si no vacío. Escapa `&`→`&amp;`, `<`→`&lt;`, `>`→`&gt;`, `\n`→`<br>`. Si hay texto: `<details class="score-breakdown" style="margin-top:0.65rem;"><summary>Descripción</summary><p style="margin-top:0.5rem;font-size:0.83rem;color:#a1a1aa;line-height:1.55;margin-bottom:0;">…</p></details>`; si no, nada.
- Card (st.markdown unsafe_allow_html, 1550-1585): `div.prop-card#card-{i}` → `prop-card-row`: `div.score-badge` (background color, `{score:.0f}`); `prop-card-body`: `<span class="prop-rank">{i+1}.</span> {título}`, `div.prop-meta` meta, `score-bar-track>score-bar-fill` width `min(score,100)%` background color; `div.prop-price`: precio `{precio:,.0f} €` (font 1.15rem/600, `#fafafa`; formato inglés con comas, NO puntos como tab1), `{eur_m2:,.0f} €/m²` (0.8rem `#71717a`), fila `ruler {m2:.0f} m²`, `bed {rooms:.0f}`, `bath {baths:.0f}` (icon size 14). Debajo: chips+warns, `_render_breakdown_html(breakdown_items, int(score))`, `_desc_html`, botón `<button class="prop-action-btn hip-btn" data-precio="{int(precio)}" data-tipo="{_t2_tipo_idx}" data-ccaa="{_t2_ccaa_idx}">€ Hipoteca</button>`.
- No hay estado vacío (df no vacío garantizado por `st.stop()` previo, app.py ~958-975), ni CSV.

## 6. TAB 3 — Evolución y análisis (`with tab3:` ~1596-1690)
- `st.write("")`; `col_c1, col_c2 = st.columns(2)`.
- **col_c1** `st.subheader("Evolución diaria")`:
  - `diario = cargar_historico()` ; si `api_datos.ApiNoDisponible` → `st.warning(f"No se pudo cargar el histórico: {e.mensaje} ({e.url}).")` y `diario = pd.DataFrame()`.
  - Si `not diario.empty and len(diario) > 1`:
    - fig1: `go.Bar(x=diario["fecha"], y=diario["count"], name="Listings", marker_color=SUBTLE, marker_line_width=0)` + `go.Scatter(x=fecha, y=avg_score, name="Score medio", yaxis="y2", line=dict(color=ACCENT,width=2.5))`; `style_fig(fig1, "Listings y score medio por día")`; layout `yaxis=dict(title=None)`, `yaxis2=dict(title=None, overlaying="y", side="right", range=[0,100], showgrid=False)`, `legend=dict(x=0.01,y=0.99)`; `st.plotly_chart(use_container_width=True)`.
    - fig2: 3 Scatter sobre `fecha`: `avg_price` mode `"lines+markers"` name "Medio" line ACCENT width 2.5; `min_price` mode "lines" name "Mínimo" line SUBTLE width 1.5 dash "dot"; `max_price` mode "lines" name "Máximo" idem. `style_fig(fig2, "Evolución de precios (€)")`.
  - Si no: `st.info("Se necesitan al menos 2 días de datos para ver evolución.")`. (Ojo: el warning de error y este info pueden mostrarse ambos.)
- **col_c2**:
  - `st.subheader("Distribución de scores")`; si `"score" in df.columns`: `px.histogram(df, x="score", nbins=20, color_discrete_sequence=[ACCENT])` sobre **df completo (incluye retirados)**; `style_fig(fig3)`; `update_traces(marker_line_width=0, opacity=0.85)`; `update_layout(xaxis_title="Score", yaxis_title=None, bargap=0.08)`.
  - `st.subheader("Top ubicaciones")`; si `"location" in df.columns`: `loc_counts = df["location"].value_counts().head(10).reset_index()`; columnas renombradas `["Ubicación","Cantidad"]`; `px.bar(x="Cantidad", y="Ubicación", orientation="h", color_discrete_sequence=[ACCENT])`; `style_fig(fig4)`; `update_traces(marker_line_width=0)`; `update_layout(xaxis_title=None, yaxis_title=None, yaxis=dict(autorange="reversed"))`. Usa `location` literal (no `zona`), top 10.
- Sin controles interactivos ni CSV.

## 7. TAB 4 — Bajadas de precio (inicio, hasta 1720)
- `with tab4:` `st.write("")`; `st.subheader("Listings con bajada de precio detectada")`; `if not bajadas.empty:` (else, fuera del rango).
- `_ORDEN_OPTS` (clave → (columna, ascendente)): `"Mayor bajada (€)": ("price_drop", False)`, `"Mayor bajada (%)": ("_pct_drop", False)`, `"Mejor score": ("score", False)`, `"Precio más bajo": ("price", True)`, `"Más reciente": ("first_seen", False)`.
- `st.selectbox("Ordenar por", list(_ORDEN_OPTS.keys()), key="b_orden")` (default = primera opción "Mayor bajada (€)").
- `bajadas_show = bajadas.copy()`; si `_sort_col == "_pct_drop"`: `_pct_drop = price_drop / (price + price_drop) * 100`; `sort_values(_sort_col, ascending=_sort_asc, na_position="last")`.
- Bucle `for _b_i, (_, row) in enumerate(bajadas_show.iterrows())` empieza con `titulo = clean(title or "Sin título") or "Sin título"`, `link_open` `<a class="prop-title" href target="_blank">`/`<span class="prop-title">` (mismo patrón que tab2). Lo demás (cards, `hip-btn` con `data-precio=int(cur)`, 1792) queda para el slice siguiente.

## Resumen de ítems
~85 ítems documentados. NO documentado: cuerpo de Novedades (tab5) — fuera del rango (está ~1850-1930); resto de tab4 desde 1720. Los números de línea de tab2/tab3 son aproximados (rango 1474-1690), los exactos de contenido leído: tab2 1473-1585, tab3 1587-1688.

---

## Inventario app.py 1590-2346 (tab3, tab4, tab5, tab6, tab7)

Nota: en el código las variables `tabN` NO siguen el orden visual. `app.py:1121`: `tab1, tab2, tab5, tab3, tab4, tab6, tab7, tab8 = st.tabs([...])` con etiquetas en orden visual (1123-1130):
1. "Listados completos" (tab1) · 2. "Top scoring" (tab2) · 3. "Novedades" (tab5) · 4. "Evolución y análisis" (tab3) · 5. "Bajadas de precio" (tab4) · 6. "Hipoteca" (tab6) · 7. "Cómo funciona" (tab7) · 8. "Mapas" (tab8).
Iconos Lucide por pestaña `_TAB_ICON_LIST` (1150-1159): layers, star, sparkles, waves, trending-down, wallet, info-circle, map-pin.
Cada `with tabN:` empieza con `st.write("")`.

## Constantes/helpers usados (definidos fuera del rango)
- Colores: `ACCENT="#6366f1"` (34), `INK="#e4e4e7"`, `MUTED="#a1a1aa"`, `SUBTLE="#52525b"` (37), `BORDER="#27272a"`, `SURFACE="#18181b"`, `GRID="#1f1f23"` (35-40).
- `SCORE_SCALE` (43-49): `[(70,"#22c55e"),(50,"#84cc16"),(35,"#eab308"),(20,"#f97316"),(0,"#ef4444")]`; `score_color(score)` (607): primer umbral con score>=umbral, fallback último color.
- `style_fig(fig, title=None)` (617-636): layout `title=dict(text=title,font=dict(size=16,color=INK,family="Fraunces"))` solo si hay título (si no `None`); `font=dict(family="Inter",size=12,color=MUTED)`; `paper_bgcolor="rgba(0,0,0,0)"`, `plot_bgcolor="rgba(0,0,0,0)"`; `margin=dict(l=12,r=12,t=44 if title else 12,b=12)`; `height=350`; `legend=dict(bgcolor="rgba(0,0,0,0)",font=dict(size=11))`; `hoverlabel=dict(bgcolor=SURFACE,bordercolor=BORDER,font=dict(family="Inter",color=INK))`; `update_xaxes(showgrid=False,zeroline=False,linecolor=BORDER,tickcolor=BORDER)`; `update_yaxes(showgrid=True,gridcolor=GRID,zeroline=False,linecolor="rgba(0,0,0,0)")`.
- `clean` (340), `zona` (388), `zona_a_ccaa` (398), `tipo_vivienda` (421), `cargar_historico` (558-561, `@st.cache_data(ttl=30)`, `api_datos.obtener_historico()`), `calc_impuestos` (791), `calc_hipoteca` (824), `hoy = date.today()` (987), `bajadas` (994-997) = `df[df["price_drop"].notna() & (df["price_drop"] > 0)]` si existe columna `price_drop`, si no `pd.DataFrame()`.
- Fiscalidad (57-63): `IVA_OBRA_NUEVA=0.10`; `ITP={"Comunidad de Madrid":0.06,"Castilla-La Mancha":0.09}`; `AJD={"Comunidad de Madrid":0.0075,"Castilla-La Mancha":0.015}`; `OTROS_GASTOS_PCT=0.015`; `TASACION_EUR=400`; `CCAA_DEFAULT="Comunidad de Madrid"`; `HIP_DEFAULTS={"entrada_pct":0.20,"plazo":30,"tin":0.03}`.
- `calc_impuestos` (791-821): precio inválido (no float, <=0, no finito) → `{"items":[],"total":0}`. Obra nueva: `iva=round(p*0.10)`, `ajd=round(p*AJD[ccaa])`, items `("IVA (10%)", iva)`, `(f"AJD ({ajd_tipo*100:.2f}% — {ccaa})", ajd)`. Segunda mano: `itp=round(p*ITP[ccaa])`, item `(f"ITP ({itp_tipo*100:.0f}% — {ccaa})", itp)`. ccaa desconocida → default Madrid.
- `calc_hipoteca` (824-877): `entrada=round(p*entrada_pct)`; `principal=round(p-entrada)`; `n=int(plazo)*12`; `r=tin/12`; `cuota = principal*r/(1-(1+r)**(-n))` si r>0 y n>0; `principal/n` si r==0, n>0; si no 0. `total_pagado_prestamo=cuota*n`; `total_intereses=max(0,total_pagado_prestamo-principal)`; `otros_gastos=round(p*0.015)+400`; `ahorro_necesario=entrada+impuestos.total+otros_gastos`. Devuelve `cuota_mensual=round(cuota)`, `total_intereses=round(..)`, `total_pagado=round(total_pagado_prestamo+entrada+impuestos.total+otros_gastos)`. Precio inválido → todo 0 con `impuestos={"items":[],"total":0}`.

---
## TAB "Evolución y análisis" = `with tab3:` (app.py:1590-1695)
Layout: `col_c1, col_c2 = st.columns(2)` (1592).

### Columna izq. (1594-1666) — `st.subheader("Evolución diaria")` (1595)
- `diario = cargar_historico()` (1597). Si `api_datos.ApiNoDisponible as e` → `st.warning(f"No se pudo cargar el histórico: {e.mensaje} ({e.url}).")` y `diario = pd.DataFrame()` (1598-1600).
- Condición: `not diario.empty and len(diario) > 1` (1601). Si no → `st.info("Se necesitan al menos 2 días de datos para ver evolución.")` (1666).
- **fig1** (1602-1633): `go.Figure` con
  - `go.Bar(x=diario["fecha"], y=diario["count"], name="Listings", marker_color=SUBTLE, marker_line_width=0)`
  - `go.Scatter(x=diario["fecha"], y=diario["avg_score"], name="Score medio", yaxis="y2", line=dict(color=ACCENT,width=2.5))` (modo por defecto de Scatter: lines)
  - `style_fig(fig1, "Listings y score medio por día")`
  - `update_layout(yaxis=dict(title=None), yaxis2=dict(title=None, overlaying="y", side="right", range=[0,100], showgrid=False), legend=dict(x=0.01, y=0.99))` — eje doble.
  - `st.plotly_chart(fig1, use_container_width=True)`
- **fig2** (1635-1664): tres `go.Scatter` sobre `diario["fecha"]`:
  - y=`avg_price`, `mode="lines+markers"`, `name="Medio"`, `line=dict(color=ACCENT,width=2.5)`
  - y=`min_price`, `mode="lines"`, `name="Mínimo"`, `line=dict(color=SUBTLE,width=1.5,dash="dot")`
  - y=`max_price`, `mode="lines"`, `name="Máximo"`, `line=dict(color=SUBTLE,width=1.5,dash="dot")`
  - `style_fig(fig2, "Evolución de precios (€)")`; sin layout extra.

### Columna dcha. (1668-1695)
- `st.subheader("Distribución de scores")` (1669). Solo si `"score" in df.columns` (1670), sin mensaje alternativo:
  - **fig3** = `px.histogram(df, x="score", nbins=20, color_discrete_sequence=[ACCENT])` (1671); `style_fig(fig3)` (sin título); `update_traces(marker_line_width=0, opacity=0.85)`; `update_layout(xaxis_title="Score", yaxis_title=None, bargap=0.08)`.
- `st.subheader("Top ubicaciones")` (1679). Solo si `"location" in df.columns`, sin mensaje alternativo:
  - `loc_counts = df["location"].value_counts().head(10).reset_index()`; columnas renombradas `["Ubicación","Cantidad"]` (1681-1682). (value_counts excluye NaN por defecto.)
  - **fig4** = `px.bar(loc_counts, x="Cantidad", y="Ubicación", orientation="h", color_discrete_sequence=[ACCENT])`; `style_fig(fig4)`; `update_traces(marker_line_width=0)`; `update_layout(xaxis_title=None, yaxis_title=None, yaxis=dict(autorange="reversed"))` (mayor arriba).
- Nota: `df` aquí es el DataFrame global (incluye todos los listings, no filtrado por tabs).

---
## TAB "Bajadas de precio" = `with tab4:` (app.py:1699-1803)
- `st.subheader("Listings con bajada de precio detectada")` (1701).
- Si `bajadas` vacío → `st.info("No se han detectado bajadas de precio todavía. Aparecerán aquí cuando un listing baje entre pasadas.")` (1800-1803).
- Widget: `st.selectbox("Ordenar por", list(_ORDEN_OPTS.keys()), key="b_orden")` (1711), default = primera opción. Opciones en orden (1704-1710), `(columna, ascending)`:
  1. "Mayor bajada (€)" → ("price_drop", False) [default]
  2. "Mayor bajada (%)" → ("_pct_drop", False)
  3. "Mejor score" → ("score", False)
  4. "Precio más bajo" → ("price", True)
  5. "Más reciente" → ("first_seen", False)
- `_pct_drop = price_drop / (price + price_drop) * 100` (1717-1722) solo si se elige esa opción. `sort_values(col, ascending=asc, na_position="last")` (1723).
- Por cada fila (1727), tarjeta `div.prop-card` (1775-1799):
  - `titulo = clean(row.get("title","Sin título")) or "Sin título"`; enlace `<a class="prop-title" href=url target="_blank">` solo si `url` es str y empieza por `http`; si no `<span class="prop-title">`.
  - `meta = " · ".join(str(clean(p) or "—") for p in [location("—"), source("—")])` + `" · {dias}d en mercado"` si hay días. `dias = (hoy - pd.Timestamp(first_seen).date()).days` si `first_seen` notna; excepción → None; texto `f"{_b_dias}d en mercado"` (vacío si None) (1766-1773).
  - `cur=price`, `drop=price_drop`, `prev=previous_price`; NaN → `cur=0`, `drop=0`, `prev = cur + drop` (reconstruir si falta) (1745-1750). `pct = drop/prev*100 if prev else 0` (1751).
  - Badge score: `score = row.get("score",0) or 0`; fondo `score_color(score)`; texto `{score:.0f}` (1753-1779).
  - Precio: anterior tachado `{prev:,.0f} €` (font-size 0.8rem, color `#a1a1aa`, `text-decoration:line-through`), actual `{cur:,.0f} €` (1.15rem, weight 600, `#fafafa`). Formato Python con coma como separador de miles (NO punto, a diferencia de tab5/tab6).
  - Badge verde `background:#15803d` con texto `−{pct:.0f}%` (carácter menos U+2212) (1788-1790).
  - Botón `<button class="prop-action-btn hip-btn" data-precio="{int(cur)}" data-tipo="{0|1}" data-ccaa="{0|1}">€ Hipoteca</button>`: `tipo_idx = 1 si tipo_vivienda(title, description, "")=="Obra nueva" else 0`; `ccaa_idx = 1 si zona_a_ccaa(zona(location,title,description))=="Castilla-La Mancha" else 0` (1755-1764).
- Navegación del botón a Hipoteca (JS 1086-1117): al clic construye `pathname?hip_precio=<precio>&hip_tipo=<["Segunda mano","Obra nueva"][tipo] URL-enc>&hip_ccaa=<["Comunidad de Madrid","Castilla-La Mancha"][ccaa] URL-enc>&hip_nav_id=<Date.now()>`, guarda `sessionStorage._sw_tab='4'` y recarga (`window.location.href`). Al cargar, el watcher (1065-1078) hace clic en `[data-baseweb="tab"][idx]` (idx 4 = 5º tab visual 0-based = "Bajadas de precio"? ver nota) — **ojo**: `idx=4` es 0-based sobre el orden visual → la pestaña 5ª "Bajadas de precio"; revisar (la pestaña Hipoteca es idx 5). Citado literal: `sessionStorage.setItem('_sw_tab','4')` (1104) y `_py_nav_tab = 4 if st.session_state.pop("_hip_py_nav", False) else "null"` (1059). Dueño de esta lógica: otra slice (1036-1117).

---
## TAB "Novedades" = `with tab5:` (app.py:1807-1935) [comentario del código dice "TAB 5: Hipoteca" (1805) pero contiene Novedades]
- `st.subheader("Pisos nuevos por pasada")` (1809).
- Si `"first_seen" not in df.columns` → `st.info("Los datos no contienen información de fecha de primera aparición.")` (1935).
- `fechas_ejecucion = sorted(df["first_seen"].dropna().dt.date.unique(), reverse=True)` (1813). Si vacío → `st.info("No hay datos de ejecuciones disponibles.")` (1933).
- Widget `st.selectbox("Pasada", fecha_labels, index=0, format_func=lambda x: x, key="nov_fecha")` (1819-1825); opciones = `str(fecha)` por fecha desc (más reciente primero). `nuevos_sel = df[df["first_seen"].dt.date == fecha_sel]`.
- Widget `st.selectbox("Ordenar por", list(_ORDEN_OPTS_N.keys()), key="nov_orden")` (1836); opciones en orden (1830-1835) `(col, ascending)`: "Mejor score"→("score",False) [default]; "Precio más bajo"→("price",True); "Mayor superficie"→("m2",False); "Más antiguo"→("first_seen",True). `sort_values(col, ascending, na_position="last")`.
- Contador (1845-1852): `div` `font-family 'Fraunces',serif; font-size 2rem; weight 400; letter-spacing -0.03em; color #fafafa; margin 0.5rem 0 1rem`: `{n_nuevos}` + `<span style="font-size:1rem;color:#a1a1aa;margin-left:0.5rem;">pisos nuevos en esta pasada</span>`.
- Vacío → `st.info("No hay pisos nuevos en esta pasada.")` (1855).
- Tarjeta por fila (1857-1931): título (`clean(title) or "Sin título"`, enlace igual que Bajadas); badge score `{sc:.0f}` con `score_color`; meta = `" · ".join(filter(None,[clean(location) or "—", clean(source) or ""]))`; detalles = `" · ".join(filter(None,[f"{int(m2)} m²", f"{int(eur_m2):,} €/m²".replace(",","."), f"{int(rooms)} hab"]))` (cada uno vacío si NaN); precio `f"{int(price):,} €".replace(",",".")` o "—"; botón `€ Hipoteca` con `data-precio = int(price) o 0`, tipo/ccaa idx igual que Bajadas.

---
## TAB "Hipoteca" = `with tab6:` (app.py:1937-2144)
- `st.subheader("Calculadora de hipoteca")` (1939).
- `precio_medio = int(df["price"].median())` si existe `price` y `notna().any()`, si no `200000` (1941-1945). Es el default del precio.
- Columnas `col_h1, col_h2, col_h3 = st.columns(3)` (1947).
- **col_h1**:
  - `st.number_input("Precio de compra (€)", min_value=10_000, max_value=5_000_000, value=precio_medio, step=5_000, format="%d", key="hip_precio")` (1949-1957).
  - Eco grande: `div` Fraunces 2.4rem, weight 400, letter-spacing -0.03em, `#fafafa`, line-height 1, margin `-0.25rem 0 1rem 0`: precio con punto de miles (`f"{int(hip_precio):,}".replace(",",".")`) + `<span style="font-size:1.1rem;color:#a1a1aa;margin-left:0.3rem;">€</span>` (1958-1967).
  - `st.radio("Tipo de vivienda", ["Segunda mano","Obra nueva"], index=0, key="hip_tipo", horizontal=True)` (1968).
  - `st.radio("Comunidad autónoma", ["Comunidad de Madrid","Castilla-La Mancha"], index=0, key="hip_ccaa", horizontal=True)` (1975).
- **col_h2**:
  - `st.slider("Entrada (%)", min_value=5, max_value=50, value=20, step=1, format="%d%%", key="hip_entrada")` (1983).
  - `st.slider("Plazo (años)", min_value=5, max_value=40, value=30, step=1, key="hip_plazo")` (1992).
- **col_h3**: `st.slider("Tipo de interés fijo (%)", min_value=0.5, max_value=8.0, value=3.0, step=0.05, format="%.2f%%", key="hip_tin")` (2001-2009).
- Cálculo (2011-2019): `hip_es_obra_nueva = hip_tipo=="Obra nueva"`; `calc_hipoteca(hip_precio, hip_entrada_pct/100, hip_plazo, hip_tin/100, hip_es_obra_nueva, hip_ccaa)`.
- Formato `_hip_eur(v) = f"{int(round(v)):,}".replace(",",".") + " €"` (2021-2022).
- **Precarga desde query params** (1038-1053): `_hip_nav_id = st.query_params.get("hip_nav_id","")`; si no vacío y `session_state["_last_hip_nav_id"] != _hip_nav_id` → lo guarda y: `session_state["hip_precio"]=int(qp["hip_precio"])` (ignora KeyError/TypeError/ValueError); si `"hip_tipo" in qp` → `session_state["hip_tipo"]=qp["hip_tipo"]`; si `"hip_ccaa" in qp` → `session_state["hip_ccaa"]=qp["hip_ccaa"]`. Solo se aplica una vez por `hip_nav_id` (para no pisar cambios del usuario). Valores esperados: tipo ∈ {"Segunda mano","Obra nueva"}, ccaa ∈ {"Comunidad de Madrid","Castilla-La Mancha"}.
- **KPIs** (2024-2038) en `div.kpi-grid` con 4 `div.kpi-card` (`kpi-icon` icono Lucide size 18, `kpi-label`, `kpi-value`), orden:
  1. icono `wallet` — "Cuota mensual" — `cuota_mensual`
  2. `zap` — "Ahorro necesario" — `ahorro_necesario`
  3. `trending-down` — "Total intereses" — `total_intereses`
  4. `building` — "Total desembolso" — `total_pagado`
- `st.markdown("**Desglose de ahorro necesario:**")` (2041).
- **Tabla desglose** (2043-2079): `tipo_txt = "Obra nueva (IVA + AJD)"` si obra nueva, si no `"Segunda mano (ITP)"`. Cabecera: "Concepto ({tipo_txt})" | "Importe". Filas en orden (`tbody`):
  1. `Entrada ({hip_entrada_pct}%)` → `entrada`
  2. filas de `impuestos["items"]` (obra nueva: `IVA (10%)`, `AJD (0.75% — Comunidad de Madrid)`/`AJD (1.50% — Castilla-La Mancha)`; segunda mano: `ITP (6% — Comunidad de Madrid)`/`ITP (9% — Castilla-La Mancha)`)
  3. `Otros gastos (gestoría, notaría, tasación…)` → `otros_gastos`
  4. fila total (`tr.sb-total`): `Ahorro necesario total` → `ahorro_necesario`
  Importes en `JetBrains Mono`, color `#a1a1aa`; contenedor `max-width:520px`, tabla fondo `#131316`, borde `1px solid #27272a`, radius 10px; cabecera fondo `#18181b`.
- `st.caption` (2081-2086) literal: "Tipos impositivos orientativos 2024-2026. ITP: C. Madrid 6% / CLM 9%. AJD (obra nueva): C. Madrid 0,75% / CLM 1,5%. IVA obra nueva: 10%. Otros gastos (~1,5% + tasación 400€) son estimaciones. Pueden existir bonificaciones por edad, familia numerosa, VPO, etc."
- **Expander** `st.expander("Gastos mensuales estimados")` (2089, colapsado por defecto), 2 columnas:
  - col_g1: `st.slider("Comunidad (€/mes)", 0, 300, 80, 5, key="g_com")`; `st.slider("IBI mensual (€/mes)", 0, 200, 50, 5, key="g_ibi")`; `st.slider("Seguro hogar (€/mes)", 0, 150, 30, 5, key="g_seg")` (formato (label, min, max, default, step)).
  - col_g2: `st.slider("Luz + gas (€/mes)", 0, 250, 80, 5, key="g_luz")`; `st.slider("Internet (€/mes)", 0, 80, 35, 5, key="g_net")`; `st.number_input("Ingresos netos mensuales (€)", min_value=500, max_value=20_000, value=2_500, step=100, key="g_ing")`.
  - Fórmulas (2107-2109): `g_gastos = comunidad+ibi+seguro+luz+internet`; `g_total = cuota_mensual + g_gastos`; `g_ratio = g_total / g_ingresos * 100 if g_ingresos > 0 else 0`.
  - Umbrales/colores (2110-2122): ratio `<30` → color `#4ade80`, bg `rgba(74,222,128,0.1)`, border `rgba(74,222,128,0.25)`; `<40` → `#fb923c`, `rgba(251,146,60,0.1)`, `rgba(251,146,60,0.25)`; `>=40` → `#f87171`, `rgba(248,113,113,0.1)`, `rgba(248,113,113,0.25)`.
  - 2 `kpi-card` (flex 1, min-width 180px) en flex con gap 1rem (2125-2143):
    1. label "Coste mensual total"; valor `_hip_eur(g_total)` (font-size 1.4rem); subtexto (0.78rem, `#71717a`): `cuota {_hip_eur(cuota_mensual)} + gastos {_hip_eur(g_gastos)}`.
    2. (fondo `g_bg`, borde `g_border`) label "Esfuerzo sobre ingresos"; valor `{g_ratio:.1f}%` coloreado `g_color` (1.4rem); subtexto "recomendado &lt; 30 %" (se ve "recomendado < 30 %").

---
## TAB "Cómo funciona" = `with tab7:` (app.py:2148-2346) (marcador 2146 "TAB 7")
- Intro `st.markdown` (2150-2158) literal: "Cada anuncio recibe una **puntuación de 0 a 100**. Lo que más pesa es si está **barato para su zona**: su precio por m² comparado con la **media de su municipio**. A eso se suman tamaño, características (con tope), señales de mercado y penalizaciones. Cuanto más alta la nota, mejor oportunidad. Así se reparten los puntos:"
- Helper `_bloque(titulo, subtitulo, items)` (2160-2174): `div.prop-card` (margin-bottom 0) con título (weight 600, `#fafafa`), subtítulo (0.8rem, `#71717a`), y filas flex space-between (borde inferior `#1f1f23`, texto `#d4d4d8`, puntos color propio weight 600, tabular-nums). Colores: `POS="#22c55e"`, `NEG="#f87171"`, `NEU="#818cf8"` (2176-2178).
- `c1, c2 = st.columns(2)` (2180). Bloques en orden (concepto, puntos, color):
  - **c1**
    1. "💎 Valor vs zona" / "€/m² frente a la media de su municipio": ("≈ 20% o más bajo la media (chollo)","+25",POS); ("En la media de su zona","≈ +12",NEU); ("≈ 20% o más por encima (caro)","+0",NEG); ("Sin m² fiable → no se puede valorar","fuera del Top",NEG)
    2. "📐 Superficie" / "Cuanto más grande, mejor": ("≥ 140 m²","+15",NEU); ("≥ 120 m²","+12",NEU); ("≥ 100 m²","+8",NEU); ("≥ 80 m²","+5",NEU)
    3. "📈 Señales de mercado" / "Cómo se comporta el anuncio en el tiempo": ("📉 Ha bajado de precio","+1 a +5",POS); ("🕸️ Lleva > 45 días anunciado","−3",NEG); ("🕸️ Lleva > 90 días anunciado","−5",NEG)
  - **c2**
    1. "✨ Características" / "Detectadas en anuncio y ficha · el total se limita a +15": ("🏊 Piscina","+15",POS); ("🚗 Garaje","+12",POS); ("📦 Trastero","+10",POS); ("🌿 Terraza / 🏡 Patio","+10",POS); ("🛗 Ascensor / 🌳 Jardín","+5",POS); ("Tope del bloque (no se acumula sin fin)","máx +15",NEU)
    2. "➕ Extras (suman)" / "Antigüedad, ubicación y calidad": ("🏗️ Obra nueva / a estrenar","+10",POS); ("🚇 Cerca de transporte público","+8",POS); ("🔧 Reformado","+5",POS); ("📅 Construido desde 2000","+1 a +5",POS); ("🏢 Ático / última planta","+3",POS); ("⚡ Eficiencia energética A/B/C","+2",POS)
    3. "⚠️ Penalizaciones (restan)" / "Avisan de posibles problemas": ("🚫 Ocupada / no admite visitas","−30",NEG); ("📍 Zona conflictiva","−3 a −20",NEG)
  - Entre bloques `st.write("")`.
- `st.write("")` + `st.markdown("##### De dónde salen los datos")` (2267-2268).
- Expanders (todos colapsados), título → contenido:
  1. "¿De qué portales vienen los anuncios?" (2270): datos de **pisos.com** (scraping fiable) e **idealista** (best-effort: si su anti-robot DataDome bloquea la pasada, esa búsqueda se omite sin interrumpir pisos.com). Campo **Source** indica origen. **Fotocasa** queda fuera por ahora (bloqueo consistente).
  2. "¿Qué municipios se rastrean?" (2278): texto "Nos centramos en municipios a **30–40 min de Madrid por autovía** (corredores A-42, A-4 y A-5). **Toledo capital queda fuera**: está a ~55 min y es un mercado distinto." Luego 2 columnas: **Madrid Sur (18)**: "Alcorcón · Arroyomolinos · Batres · Ciempozuelos · Cubas de la Sagra · Fuenlabrada · Getafe · Griñón · Humanes de Madrid · Leganés · Móstoles · Moraleja de Enmedio · Navalcarnero · Parla · Pinto · Serranillos del Valle · Torrejón de la Calzada · Valdemoro"; **Toledo Norte (5)**: "Esquivias · Illescas · Seseña · Ugena · Yeles".
  3. "¿Cómo se asegura que el precio es real?" (2298): el listado a veces muestra precios "desde"; el sistema puntúa todos, **visita la ficha completa de los mejores** y re-puntúa con datos reales (precio, metros, habitaciones, baños, año, estado de conservación); por eso algún anuncio puede aparecer algo por encima de 300.000 € (su precio real subió) pero si su €/m² es bueno se mantiene.
  4. '¿Qué significa "barato para su zona"?' (2308): factor que más pesa; cada pasada calcula la **mediana de €/m² de cada municipio**; compara; por debajo = chollo y sube, por encima baja; si el municipio tiene pocos anuncios usa la media de su **zona** (Madrid Sur / Toledo Norte). **Matiz**: media sobre anuncios de hasta 300.000 € → referencia del *segmento asequible*.
  5. '¿Por qué algunos salen como "sin valorar"?' (2318): sin **m² fiables** (faltan o absurdos) no se calcula €/m²; se marcan **"s/valorar"**, quedan **fuera del Top**, no cuentan en el "Score medio", pero siguen guardados.
  6. "¿De dónde vienen los datos del mapa de seguridad?" (2325): **Vista criminalidad (por municipio)**: tasa oficial (infracciones penales × 100 000 hab) del **Portal Estadístico de Criminalidad** del Ministerio del Interior; solo municipios con más de **20 000 habitantes**, los pueblos pequeños de la Sagra toledana aparecen en gris; "La tasa se calcula anualizado datos de Q1 2026. Fuente: estadisticasdecriminalidad.ses.mir.es". **Vista renta (por sección censal / barrio)**: **renta neta media por persona** del **Atlas de Distribución de Renta de los Hogares (ADRH 2023)** INE oct 2025; sección censal ~1 000–2 500 hab; diferencias **dentro** de cada municipio. "Verde = renta alta (barrio acomodado), rojo = renta baja. ⚠️ Renta no equivale directamente a criminalidad — es un **proxy socioeconómico del barrio**, no un dato policial. Fuente: ine.es/experimental/atlas".
- Pie (2344-2346) `st.caption("La puntuación es orientativa: ayuda a priorizar, no sustituye una visita.")`.

## Observaciones de paridad
- Formatos numéricos: Bajadas usa coma de miles (`{:,.0f}`); Novedades e Hipoteca usan punto (`.replace(",", ".")`).
- Tab Hipoteca y botón € en Bajadas/Novedades/Top: la navegación usa query params + sessionStorage (1042-1117), responsabilidad de otra slice.
- `hoy` y `df`, `bajadas` son globales (987, 994).

---

## Inventario `with tab8:` (Mapas) + footer — app.py:2348-2724

## 0. Imports/constantes usadas
- app.py:8-19 imports: re, json, math, base64, unicodedata, pandas as pd, plotly.express as px, plotly.graph_objects as go, streamlit, Path, date/datetime; `import api_datos` (:21).
- app.py:30 `ASSETS_DIR = Path(__file__).resolve().parent / "assets"`.
- Paleta (app.py:34-40): ACCENT `#6366f1`, INK `#e4e4e7`, MUTED `#a1a1aa`, SUBTLE `#52525b`, BORDER `#27272a`, SURFACE `#18181b`, GRID `#1f1f23`.
- Comentario cabecera: `# ── TAB 8: Mapa de seguridad ──` (app.py:2348); `with tab8:` (:2350); primera línea `st.write("")` (:2351).

## 1. Carga de assets (app.py:2353-2369; loaders app.py:564-604)
- Rutas: `municipios_zona.geojson`, `criminalidad.csv`, `secciones_renta.geojson` en ASSETS_DIR (:2354-2356).
- Los loaders reciben `mtime` del fichero (0.0 si no existe) sólo para invalidar caché `@st.cache_data` (:2358-2366).
- `cargar_geojson_municipios` (:565): si no existe → `None`; si no, `json.loads(read_text utf-8)`.
- `cargar_criminalidad` (:574): no existe → `pd.DataFrame()` vacío; `pd.read_csv(path, comment="#")` (líneas `#` ignoradas); `tasa_criminalidad = pd.to_numeric(..., errors="coerce")`.
- `cargar_secciones_renta` (:588): no existe → `(None, pd.DataFrame())`; carga geojson; `rows=[feat["properties"] for feat in gj.get("features", [])]`; si `rows` vacío → `(gj, pd.DataFrame())`; si no, `df_r=pd.DataFrame(rows)`, `renta_persona = pd.to_numeric(errors="coerce")`; devuelve `(gj, df_r)`.
- Flags: `_tiene_criminalidad = geojson_mun is not None and not df_crim.empty` (:2368); `_tiene_renta = geojson_sec is not None and not df_renta.empty` (:2369).
- Joins/claves: criminalidad: `df_crim.cod_ine` ↔ `geojson_mun.features[].properties.cod_ine` (`featureidkey="properties.cod_ine"`). Renta: `df_renta.cusec` ↔ `geojson_sec properties.cusec` (`featureidkey="properties.cusec"`). Precio: `df.municipio` (slug) → `cod_ine` vía nombre GeoJSON slugificado ↔ `properties.cod_ine`.
- Nota: `cod_ine` en CSV se lee por pandas como int (p.ej. 28007) y en el geojson es string ("28007"); plotly `locations` se empareja con id de feature como string (comportamiento de plotly). En `crim_codes` se usa `.astype(str)` (:2484) para comparar con strings del geojson.

## 2. Estado vacío (app.py:2371-2375)
- Si `not _tiene_criminalidad and not _tiene_renta` → `st.warning` con texto literal:
  "Activos del mapa no encontrados. Ejecuta primero el script de build:\n\n```\ncd house-dashboard/dashboard\npython scripts/build_mapa_assets.py\n```"
- `else:` (:2376) → resto de la UI.

## 3. Selector de capa (app.py:2377-2392)
- Lista `_opciones` dinámica, en este orden:
  1. si `_tiene_criminalidad`: `"🔴  Criminalidad · por municipio"` (dos espacios tras emoji) (:2380)
  2. si `_tiene_renta`: `"🟢  Renta · por barrio (sección censal)"` (:2382)
  3. siempre: `"🟡  Precio vivienda · por municipio"` (:2383)
- `st.radio("Capa", _opciones, horizontal=True, label_visibility="collapsed")` (:2385-2390). Sin `key`. Default = primera opción (index 0) → criminalidad si hay datos; si no, renta; si no, precio.
- `_modo_renta = _capa.startswith("🟢")`; `_modo_precios = _capa.startswith("🟡")` (:2391-2392).
- Rama de vista: A criminalidad si `not _modo_renta and not _modo_precios and _tiene_criminalidad` (:2446); B renta `elif _modo_renta and _tiene_renta` (:2519); `elif _modo_renta and not _tiene_renta` warning (:2596); C `elif _modo_precios` (:2605).

## 4. Constantes compartidas (app.py:2394-2441)
- `_CRIM_COLOR_SCALE` (:2395): `[0.0,"#22c55e"],[0.35,"#84cc16"],[0.55,"#eab308"],[0.75,"#f97316"],[1.0,"#ef4444"]` (verde seguro → rojo peligroso).
- `_RENTA_COLOR_SCALE` (:2405): `[0.0,"#ef4444"],[0.25,"#f97316"],[0.5,"#eab308"],[0.75,"#84cc16"],[1.0,"#22c55e"]` (rojo renta baja → verde alta).
- `_PRECIO_COLOR_SCALE` (:2642, dentro vista C): `[0.0,"#22c55e"],[0.35,"#84cc16"],[0.55,"#eab308"],[0.75,"#f97316"],[1.0,"#ef4444"]` (verde más barato → rojo más caro) — igual que criminalidad.
- `_MAP_LAYOUT` (:2413): `paper_bgcolor="rgba(0,0,0,0)"`, `plot_bgcolor="rgba(0,0,0,0)"`, `margin=dict(l=0,r=0,t=0,b=48)`, `height=540`, `font=dict(family="Inter", size=12, color=MUTED)`, `hoverlabel=dict(bgcolor=SURFACE, bordercolor=BORDER, font=dict(family="Inter", color=INK))`.
- `_colorbar(title_text)` (:2426): `dict(orientation="h", x=0.5, xanchor="center", y=-0.04, yanchor="top", thickness=10, len=0.72, title=title_text, title_side="top", tickfont=dict(color=MUTED,size=10), title_font=dict(color=MUTED,size=11), bgcolor="rgba(0,0,0,0)", bordercolor=BORDER)`. Se aplica con `fig.update_layout(**_MAP_LAYOUT, coloraxis_colorbar=_colorbar(...))`.
- Común a los 3 mapas: `center={"lat": 40.18, "lon": -3.78}`, `map_style="carto-darkmatter"`, `opacity=0.75`, `px.choropleth_map`, `st.plotly_chart(fig, use_container_width=True)`. Municipios/secciones sin fila en el DataFrame no se pintan (fondo del mapa oscuro; el texto los llama "gris").

## 5. Vista A — Criminalidad (app.py:2443-2514)
- `periodo = df_crim["periodo"].iloc[0]` si existe columna `periodo`, si no `"Q1 2026"` (:2447-2451).
- `tasa_max = df_crim["tasa_criminalidad"].max()`, `tasa_min = ...min()` (:2452-2453).
- `px.choropleth_map(df_crim, geojson=geojson_mun, locations="cod_ine", featureidkey="properties.cod_ine", color="tasa_criminalidad", color_continuous_scale=_CRIM_COLOR_SCALE, range_color=(tasa_min*0.85, tasa_max*1.05), hover_name="municipio", hover_data={"cod_ine": False, "tasa_criminalidad": ":.0f", "periodo": True}, labels={"tasa_criminalidad": "Tasa / 100 000 hab", "periodo": "Período"}, center={"lat":40.18,"lon":-3.78}, zoom=9, map_style="carto-darkmatter", opacity=0.75)` (:2455-2477).
- Colorbar título: `"Tasa / 100 000 hab"` (:2480).
- Municipios sin dato: `crim_codes = set(df_crim["cod_ine"].astype(str))`; `sin_dato = sorted(f["properties"]["nombre"] for f in geojson_mun["features"] if f["properties"]["cod_ine"] not in crim_codes)` (:2484-2489).
- `st.caption` literal (concatenado, :2490-2496): `**Fuente**: Portal Estadístico de Criminalidad · Ministerio del Interior · **Período**: {periodo} · **Métrica**: infracciones penales / 100 000 hab · **Rojo** = más peligroso · **Verde** = más seguro · **Gris** = sin publicación oficial (<20 000 hab)`.
- `st.expander(f"Municipios sin datos oficiales ({len(sin_dato)} en gris)")` (:2497): contenido `st.write(", ".join(sin_dato) if sin_dato else "Todos tienen datos.")` (:2500) (colapsado por defecto).
- `st.write("")`; `st.subheader("Ranking de peligrosidad")` (:2502-2503).
- Tabla ranking (:2504-2514): `df_crim[["municipio","tasa_criminalidad"]].sort_values("tasa_criminalidad", ascending=False).reset_index(drop=True)`; `index += 1` (posición 1-based visible, `hide_index=False`); columnas renombradas `["Municipio", "Tasa / 100 000 hab"]`; tasa formateada `"{:.0f}".format` (string, sin decimales ni separador de miles); `st.dataframe(..., use_container_width=True, hide_index=False)`.
- Nota: no hay filtrado de NaN en vista A (si tasa NaN, `.map("{:.0f}".format)` daría "nan"; `max/min` ignoran NaN). Los datos actuales no tienen NaN.

## 6. Vista B — Renta por sección censal (app.py:2516-2594)
- `df_r = df_renta.dropna(subset=["renta_persona"])`; `renta_min/max` de `df_r["renta_persona"]` (:2520-2522).
- `px.choropleth_map(df_r, geojson=geojson_sec, locations="cusec", featureidkey="properties.cusec", color="renta_persona", color_continuous_scale=_RENTA_COLOR_SCALE, range_color=(renta_min*0.9, renta_max*1.05), hover_name="municipio", hover_data={"cusec": True, "renta_persona": ":,.0f", "anio": True}, labels={"renta_persona": "Renta neta media (€/pers)", "cusec": "Sección censal", "anio": "Año"}, center={"lat":40.18,"lon":-3.78}, zoom=10, map_style="carto-darkmatter", opacity=0.75)` (:2524-2547).
- Colorbar título: `"Renta neta media (€/pers)"` (:2550).
- `total_sec = len(df_renta)`; `sin_renta = total_sec - len(df_r)` (:2555-2556); `_anio_renta = df_renta["anio"].iloc[0]` si hay columna `anio`, si no `"2023"` (:2557-2559).
- `st.caption` literal (:2560-2566): `**Fuente**: Atlas de Distribución de Renta de los Hogares (ADRH {_anio_renta}) · INE · **Métrica**: renta neta media por persona (€/año) · **Verde** = renta alta · **Rojo** = renta baja · **Gris** = sin publicación oficial ({sin_renta} secciones) · ⚠️ Renta ≠ criminalidad — proxy socioeconómico del barrio`.
- Si `sin_renta` > 0: `st.expander(f"Secciones sin dato de renta ({sin_renta} en gris)")` con `st.dataframe(df_renta[df_renta["renta_persona"].isna()][["municipio","cusec"]].sort_values("municipio").reset_index(drop=True), use_container_width=True, hide_index=True)` (:2567-2576). (Datos actuales: 0 nulos → expander no se muestra.)
- `st.write("")`; `st.subheader("Ranking de barrios por renta")` (:2578-2579).
- Ranking (:2580-2594): `df_r[["municipio","cusec","renta_persona"]].sort_values("renta_persona", ascending=False).reset_index(drop=True)`; `index += 1`; columnas `["Municipio","Sección censal","Renta neta media (€/pers)"]`; renta formateada `"{:,.0f}".format` (separador de miles inglés `17,093`); `st.dataframe(use_container_width=True, hide_index=False)`. Todas las 953 secciones (sin top-N).
- Rama sin asset (:2596-2600): `st.warning("Asset de renta por sección no encontrado. Ejecuta el script de build:\n\n```\ncd house-dashboard/dashboard\npython scripts/build_mapa_assets.py\n```")`. (Inalcanzable por UI normal porque la opción renta no aparece sin `_tiene_renta`.)

## 7. Vista C — Precio vivienda por municipio (app.py:2602-2714)
- Si `geojson_mun is None` → `st.warning("GeoJSON de municipios no encontrado. Ejecuta el script de build:\n\n```\ncd house-dashboard/dashboard\npython scripts/build_mapa_assets.py\n```")` (:2606-2610).
- `_slug_muni(nombre)` (:2613): `unicodedata.normalize("NFD", nombre.lower())`; quitar chars con `unicodedata.category(c) == "Mn"`; `.replace(" ","_").replace("-","_").replace("'","")`.
- `_slug_to_cod = {_slug_muni(f.properties.nombre): f.properties.cod_ine for f in geojson_mun.features}` (:2618); `_cod_to_nombre = {cod_ine: nombre}` (:2622).
- Agregado (:2628-2637) sobre el DataFrame global `df` (anuncios scrapeados, definido fuera de tab8): `df[df["eur_m2"].notna() & df["municipio"].notna()].groupby("municipio").agg(eur_m2_med=("eur_m2","median"), precio_med=("price","median"), n_listings=("price","count")).reset_index()`.
- `_df_p["cod_ine"] = _df_p["municipio"].map(_slug_to_cod)`; `dropna(subset=["cod_ine"])`; `_df_p["nombre"] = _df_p["cod_ine"].map(_cod_to_nombre)` (:2638-2640).
- `_p_min/_p_max = _df_p["eur_m2_med"].min()/.max()` (:2650-2651).
- `px.choropleth_map(_df_p, geojson=geojson_mun, locations="cod_ine", featureidkey="properties.cod_ine", color="eur_m2_med", color_continuous_scale=_PRECIO_COLOR_SCALE, range_color=(_p_min*0.9, _p_max*1.05), hover_name="nombre", hover_data={"cod_ine": False, "eur_m2_med": ":,.0f", "precio_med": ":,.0f", "n_listings": True}, labels={"eur_m2_med": "€/m² (mediana)", "precio_med": "Precio mediano (€)", "n_listings": "Anuncios"}, center={"lat":40.18,"lon":-3.78}, zoom=9, map_style="carto-darkmatter", opacity=0.75)` (:2653-2677).
- Colorbar título: `"€/m² mediana"` (:2680).
- `_n_mun = len(_df_p)`; `_total_mun = len(geojson_mun["features"])`; `_sin_precio = _total_mun - _n_mun` (:2684-2686).
- `st.caption` literal (:2687-2692): `**Fuente**: anuncios scrapeados (pisos.com + idealista) · **Métrica**: mediana de €/m² por municipio · **Verde** = más barato · **Rojo** = más caro · **Gris** = sin anuncios ({_sin_precio} municipios)`.
- `st.write("")`; `st.subheader("Ranking de precio por municipio")` (:2694-2695).
- Ranking (:2696-2714): `_df_p[["nombre","eur_m2_med","precio_med","n_listings"]].sort_values("eur_m2_med", ascending=True)` (¡ascendente: más barato primero!) `.reset_index(drop=True)`; `index += 1`; columnas `["Municipio","€/m² mediana","Precio mediano (€)","Anuncios"]`; `€/m² mediana` y `Precio mediano (€)` formateados `"{:,.0f}".format`; `Anuncios` entero sin formato; `st.dataframe(use_container_width=True, hide_index=False)`.
- Esta vista NO está filtrada por sidebar/filtros salvo que el `df` global ya lo esté (verificar en slice base: `df` usado aquí es el nombre global en :2629; otra slice debe documentar si es filtrado).
- Nota: vista C no usa la API de mapas ni assets CSV; sólo geojson de municipios.

## 8. Footer (app.py:2716-2724) — a nivel módulo (fuera de tabs)
- `st.write("")`; `st.divider()` (:2718-2719).
- `st.caption(` (:2720) f-string: `Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} · Datos de la API en `{api_datos.url_api()}` · [Forzar recarga](?rerun) · Scorer: property_scorer_all.py (pisos.com + idealista · Madrid Sur + Toledo Norte · ≤ 300.000 €)`.
- Hora = hora local del servidor en cada rerun. `api_datos.url_api()` definida en api_datos.py (otro slice). El enlace `?rerun` es markdown link relativo (recarga la página). No hay scripts/JS posteriores; EOF = línea 2724.

## 9. Schemas de assets
### criminalidad.csv (12 filas de datos)
- Cabecera con 4 líneas de comentario `#`: `# Tasa de criminalidad por municipio` / `# Fuente: Portal Estadístico de Criminalidad - Ministerio del Interior` / `# Periodo: Q1 2026 (ene-mar), anualizado` / `# Municipios sin publicacion oficial (<20 000 hab) no aparecen en este fichero`.
- Línea cabecera CSV: `cod_ine,municipio,tasa_criminalidad,periodo,fuente`
- Ejemplo: `28007,Alcorcón,3295.6,"Q1 2026 (ene-mar), anualizado","Portal Estadístico de Criminalidad - Ministerio del Interior"`; `28040,Ciempozuelos,4197.5,…`; `28058,Fuenlabrada,2164.3,…`; última fila `45161,Seseña,5480.9,…`. Valores `periodo` = `Q1 2026 (ene-mar), anualizado` (contiene coma, entrecomillado). Parser web debe soportar comentarios `#` y campos entrecomillados.
### municipios_zona.geojson
- `FeatureCollection`, 47 features, sin otras claves de raíz. Geometrías `Polygon` y `MultiPolygon`.
- `properties`: `{cod_ine: string (p.ej. "45056"), nombre: string (p.ej. "Chozas de Canales")}`.
### secciones_renta.geojson
- `FeatureCollection`, 953 features (geometría Polygon en la primera), sin otras claves de raíz; 47 `cod_ine` distintos.
- `properties`: `{cusec: string 10 dígitos ("2800701001"), cod_ine: string ("28007"), municipio: string ("Alcorcón"), renta_persona: number (int o float; "17093.34"), anio: string ("2023")}`.
- Actualmente 0 secciones con `renta_persona` null; valores de `anio`: sólo `"2023"`.

## 10. Expander informativo previo (cierre de tab7, app.py:2325-2346; contexto del mismo origen)
- Aparece al final de tab7 (otro slice), texto sobre mapa de seguridad: ver app.py:2325-2342 (`"¿De dónde vienen los datos del mapa de seguridad?"`), y `st.caption("La puntuación es orientativa: ayuda a priorizar, no sustituye una visita.")` (:2344-2346). Notar que el texto dice "Q1 2026" y "estadisticasdecriminalidad.ses.mir.es", "ine.es/experimental/atlas".
