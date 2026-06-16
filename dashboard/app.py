"""
Dashboard de Búsqueda de Vivienda — Madrid Sur + Toledo Norte
Hecho a medida del property_scorer.py (pisos.com scraping + scoring)

Lanzar: streamlit run app.py
"""

import re
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path
from datetime import date, datetime

st.set_page_config(
    page_title="Búsqueda de Vivienda",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed",
)

DATA_DIR = Path(__file__).resolve().parent.parent / "datos"

# ── Paleta semántica ─────────────────────────────────────────────

ACCENT = "#6366f1"          # indigo-500 — único color de acento
INK = "#e4e4e7"             # zinc-200 (texto principal)
MUTED = "#a1a1aa"           # zinc-400
SUBTLE = "#52525b"          # zinc-600
BORDER = "#27272a"          # zinc-800
SURFACE = "#18181b"         # zinc-900 (tarjetas)
GRID = "#1f1f23"            # rejilla apenas perceptible

# Escala de score sobria (tonos apagados, sin colores chillones)
SCORE_SCALE = [
    (70, "#22c55e"),
    (50, "#84cc16"),
    (35, "#eab308"),
    (20, "#f97316"),
    (0, "#ef4444"),
]

# Secuencia neutra para series de datos
SERIES = ["#6366f1", "#94a3b8", "#22d3ee", "#a78bfa", "#2dd4bf", "#94a3b8"]


# ── Iconos vectoriales (Lucide, inline SVG, stroke 1.75) ─────────

_ICON_PATHS = {
    "layers": '<path d="M12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.84Z"/><path d="m22 17.65-9.17 4.16a2 2 0 0 1-1.66 0L2 17.65"/><path d="m22 12.65-9.17 4.16a2 2 0 0 1-1.66 0L2 12.65"/>',
    "sparkles": '<path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .962 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.582a.5.5 0 0 1 0 .962L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.962 0z"/>',
    "star": '<path d="M11.525 2.295a.53.53 0 0 1 .95 0l2.31 4.679a2.12 2.12 0 0 0 1.595 1.16l5.166.756a.53.53 0 0 1 .294.904l-3.736 3.638a2.12 2.12 0 0 0-.611 1.878l.882 5.14a.53.53 0 0 1-.771.56l-4.618-2.428a2.12 2.12 0 0 0-1.973 0L6.396 21.01a.53.53 0 0 1-.77-.56l.881-5.139a2.12 2.12 0 0 0-.611-1.879L2.16 9.795a.53.53 0 0 1 .294-.906l5.165-.755a2.12 2.12 0 0 0 1.597-1.16z"/>',
    "wallet": '<path d="M19 7V4a1 1 0 0 0-1-1H5a2 2 0 0 0 0 4h15a1 1 0 0 1 1 1v4h-3a2 2 0 0 0 0 4h3a1 1 0 0 0 1-1v-2a1 1 0 0 0-1-1"/><path d="M3 5v14a2 2 0 0 0 2 2h15a1 1 0 0 0 1-1v-4"/>',
    "trending-down": '<path d="M16 17h6v-6"/><path d="m22 17-8.5-8.5-5 5L2 7"/>',
    "waves": '<path d="M2 6c.6.5 1.2 1 2.5 1C7 7 7 5 9.5 5s2.4 2 5 2 2.5-2 5-2c1.3 0 1.9.5 2.5 1"/><path d="M2 12c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2s2.4 2 5 2 2.5-2 5-2c1.3 0 1.9.5 2.5 1"/><path d="M2 18c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2s2.4 2 5 2 2.5-2 5-2c1.3 0 1.9.5 2.5 1"/>',
    "map-pin": '<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/>',
    "building": '<path d="M6 22V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v18Z"/><path d="M6 12H4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2"/><path d="M18 9h2a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-2"/><path d="M10 6h4"/><path d="M10 10h4"/><path d="M10 14h4"/><path d="M10 18h4"/>',
    "calendar": '<path d="M8 2v4"/><path d="M16 2v4"/><rect width="18" height="18" x="3" y="4" rx="2"/><path d="M3 10h18"/>',
    "zap": '<path d="M4 14a1 1 0 0 1-.78-1.63l9.9-10.2a.5.5 0 0 1 .86.46l-1.92 6.02A1 1 0 0 0 13 10h7a1 1 0 0 1 .78 1.63l-9.9 10.2a.5.5 0 0 1-.86-.46l1.92-6.02A1 1 0 0 0 11 14z"/>',
    "ruler": '<path d="M21.3 15.3a2.4 2.4 0 0 1 0 3.4l-2.6 2.6a2.4 2.4 0 0 1-3.4 0L2.7 8.7a2.41 2.41 0 0 1 0-3.4l2.6-2.6a2.41 2.41 0 0 1 3.4 0Z"/><path d="m14.5 12.5 2-2"/><path d="m11.5 9.5 2-2"/><path d="m8.5 6.5 2-2"/><path d="m17.5 15.5 2-2"/>',
    "bed": '<path d="M2 4v16"/><path d="M2 8h18a2 2 0 0 1 2 2v10"/><path d="M2 17h20"/><path d="M6 8v9"/>',
    "bath": '<path d="M10 4 8 6"/><path d="M17 19v2"/><path d="M2 12h20"/><path d="M7 19v2"/><path d="M9 5 7.5 3.5a1.5 1.5 0 0 0-3 0V12"/><path d="M22 12v3a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4v-3"/>',
}


def icon(name, size=16, color="currentColor", stroke=1.75):
    paths = _ICON_PATHS.get(name, "")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="{stroke}" '
        f'stroke-linecap="round" stroke-linejoin="round" '
        f'style="vertical-align:-2px;flex-shrink:0;">{paths}</svg>'
    )


# ── Estilos premium (CSS) ────────────────────────────────────────

def inject_styles():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        html, body, [class*="css"], .stMarkdown, .stMetric {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }

        .stApp { background: #09090b; }
        .block-container { padding-top: 3rem; padding-bottom: 4rem; max-width: 1320px; }

        h1 { font-weight: 700; letter-spacing: -0.02em; color: #fafafa; }
        h2, h3 { font-weight: 600; letter-spacing: -0.01em; color: #e4e4e7; }

        /* Tarjetas de métrica */
        [data-testid="stMetric"] {
            background: #18181b;
            border: 1px solid #27272a;
            border-radius: 16px;
            padding: 1.1rem 1.25rem;
            box-shadow: 0 1px 2px rgba(0,0,0,0.3);
            transition: all 200ms ease-in-out;
        }
        [data-testid="stMetric"]:hover {
            border-color: #3f3f46;
            box-shadow: 0 4px 14px rgba(0,0,0,0.4);
        }
        [data-testid="stMetricLabel"] {
            font-size: 0.78rem; font-weight: 500; color: #a1a1aa;
            text-transform: uppercase; letter-spacing: 0.04em;
        }
        [data-testid="stMetricValue"] {
            font-size: 1.6rem; font-weight: 600; color: #fafafa;
        }

        /* Pestañas */
        .stTabs [data-baseweb="tab-list"] { gap: 0.25rem; border-bottom: 1px solid #27272a; }
        .stTabs [data-baseweb="tab"] {
            font-weight: 500; color: #a1a1aa; padding: 0.6rem 1rem;
            border-radius: 8px 8px 0 0;
        }
        .stTabs [aria-selected="true"] { color: #818cf8; font-weight: 600; }

        /* Tarjeta de listado */
        .prop-card {
            background: #18181b; border: 1px solid #27272a; border-radius: 16px;
            padding: 1.25rem 1.5rem; margin-bottom: 0.9rem;
            box-shadow: 0 1px 2px rgba(0,0,0,0.3);
            transition: all 200ms ease-in-out;
        }
        .prop-card:hover { border-color: #3f3f46; box-shadow: 0 6px 18px rgba(0,0,0,0.45); }

        .prop-rank { color: #71717a; font-weight: 600; font-size: 0.9rem; }
        .prop-title { font-weight: 600; font-size: 1.02rem; color: #fafafa; text-decoration: none; }
        .prop-title:hover { color: #818cf8; }
        .prop-meta {
            color: #a1a1aa; font-size: 0.84rem; margin-top: 0.4rem;
            display: flex; flex-wrap: wrap; gap: 0.35rem 1rem;
        }
        .meta-item { display: inline-flex; align-items: center; gap: 0.35rem; }
        .meta-item svg { color: #71717a; }

        /* KPIs personalizados con icono */
        .kpi-grid {
            display: grid; grid-template-columns: repeat(6, 1fr);
            gap: 0.85rem; margin-bottom: 0.5rem;
        }
        @media (max-width: 1100px) { .kpi-grid { grid-template-columns: repeat(3, 1fr); } }
        @media (max-width: 640px)  { .kpi-grid { grid-template-columns: repeat(2, 1fr); } }
        .kpi-card {
            background: #18181b; border: 1px solid #27272a; border-radius: 16px;
            padding: 1.1rem 1.2rem; transition: all 200ms ease-in-out;
        }
        .kpi-card:hover { border-color: #3f3f46; box-shadow: 0 4px 14px rgba(0,0,0,0.4); }
        .kpi-icon {
            display: inline-flex; align-items: center; justify-content: center;
            width: 34px; height: 34px; border-radius: 10px;
            background: rgba(99,102,241,0.12); color: #818cf8; margin-bottom: 0.7rem;
        }
        .kpi-label {
            font-size: 0.72rem; font-weight: 500; color: #a1a1aa;
            text-transform: uppercase; letter-spacing: 0.05em;
        }
        .kpi-value { font-size: 1.55rem; font-weight: 600; color: #fafafa; margin-top: 0.1rem; }

        .score-badge {
            display: inline-flex; align-items: center; justify-content: center;
            min-width: 48px; height: 48px; border-radius: 12px;
            font-weight: 700; font-size: 1.2rem; color: #09090b;
        }
        .score-bar-track {
            width: 100%; height: 5px; background: #27272a;
            border-radius: 999px; margin-top: 0.5rem; overflow: hidden;
        }
        .score-bar-fill { height: 100%; border-radius: 999px; }

        .chip {
            display: inline-block; padding: 0.2rem 0.65rem; margin: 0.15rem 0.2rem 0.15rem 0;
            background: #27272a; border: 1px solid #3f3f46; border-radius: 999px;
            font-size: 0.78rem; color: #d4d4d8; font-weight: 500;
        }
        .chip-warn { background: #2a1215; border-color: #5b1d22; color: #fca5a5; }

        /* Botones */
        .stButton button, .stDownloadButton button {
            border-radius: 10px; border: 1px solid #27272a; font-weight: 500;
            background: #18181b; color: #e4e4e7;
            transition: all 200ms ease-in-out;
        }
        .stDownloadButton button:hover { border-color: #6366f1; color: #818cf8; }

        /* Divisores más sutiles */
        hr { border-color: #27272a !important; }

        #MainMenu, footer { visibility: hidden; }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ── Utilidades de limpieza ───────────────────────────────────────

_EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF"
    "\U00002190-\U000021FF\U00002B00-\U00002BFF️‍]",
    flags=re.UNICODE,
)


def clean(text):
    """Quita emojis y espacios sobrantes de un string para mostrar en UI."""
    if not isinstance(text, str):
        return text
    return _EMOJI_RE.sub("", text).strip(" ·")


# ── Carga de datos ──────────────────────────────────────────────

@st.cache_data(ttl=30)
def cargar_datos():
    if not DATA_DIR.exists():
        return pd.DataFrame()

    todos = []
    for f in sorted(DATA_DIR.glob("*.json")):
        try:
            listings = json.loads(f.read_text(encoding="utf-8"))
            for item in listings:
                item["_archivo"] = f.stem
                todos.append(item)
        except (json.JSONDecodeError, IOError):
            continue

    if not todos:
        return pd.DataFrame()

    df = pd.DataFrame(todos)
    for col in ["price", "m2", "rooms", "bathrooms", "score", "year_built", "price_drop", "previous_price"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "first_seen" in df.columns:
        df["first_seen"] = pd.to_datetime(df["first_seen"], errors="coerce")
    if "last_seen" in df.columns:
        df["last_seen"] = pd.to_datetime(df["last_seen"], errors="coerce")
    if "_archivo" in df.columns:
        df["_archivo"] = pd.to_datetime(df["_archivo"], errors="coerce")

    if "price" in df.columns and "m2" in df.columns:
        df["eur_m2"] = (df["price"] / df["m2"]).round(0)

    return df.sort_values("score", ascending=False, na_position="last")


def score_color(score):
    for threshold, color in SCORE_SCALE:
        if score >= threshold:
            return color
    return SCORE_SCALE[-1][1]


# ── Plotly: plantilla limpia ─────────────────────────────────────

def style_fig(fig, title=None):
    fig.update_layout(
        title=dict(text=title, font=dict(size=15, color=INK, family="Inter")) if title else None,
        font=dict(family="Inter", size=12, color=MUTED),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=12, r=12, t=44 if title else 12, b=12),
        height=350,
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
        hoverlabel=dict(bgcolor=SURFACE, bordercolor=BORDER, font=dict(family="Inter", color=INK)),
    )
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor=BORDER, tickcolor=BORDER)
    fig.update_yaxes(showgrid=True, gridcolor=GRID, zeroline=False, linecolor="rgba(0,0,0,0)")
    return fig


# ── Extraer features del score_details ──────────────────────────

def parse_score_details(prop):
    """Parsea score_details (marcadores con emoji del scraper) en categorías."""
    details = prop.get("score_details", [])
    features, penalties, bonuses = [], [], []
    for d in details:
        if "⚠️" in d:
            penalties.append(clean(d))
        elif any(e in d for e in ["🏊", "🚗", "📦", "🌿", "🏡", "🛗", "🌳", "🏗️", "🔧", "🚇", "🏢", "⚡", "📅"]):
            features.append(clean(d))
        elif "💰" in d or "📐" in d:
            bonuses.append(clean(d))
    return features, penalties, bonuses


# ── UI ───────────────────────────────────────────────────────────

inject_styles()

st.title("Búsqueda de Vivienda")
st.caption("Madrid Sur · Toledo Norte — pisos.com · Scoring a medida · Hasta 250.000 €")

df = cargar_datos()

if df.empty:
    st.warning("No hay datos todavía. Ejecuta primero el scraper:")
    st.code("python ~/AppData/Local/hermes/scripts/property_scorer.py")
    st.info("Luego guarda los resultados con: python dashboard/guardar.py ~/AppData/Local/hermes/last_property_data.json")
    st.stop()

# ── KPIs ─────────────────────────────────────────────────────────

hoy = date.today()
df_hoy = df[df["_archivo"] == pd.Timestamp(hoy)] if "_archivo" in df.columns else pd.DataFrame()
nuevos_hoy = df[df["first_seen"] == pd.Timestamp(hoy)] if "first_seen" in df.columns else pd.DataFrame()
bajadas = df[df["price_drop"].notna() & (df["price_drop"] > 0)] if "price_drop" in df.columns else pd.DataFrame()
con_piscina = len([p for p in df.to_dict("records") if "piscina" in str(p.get("detail_features", {})).lower() or "piscina" in str(p.get("features", [])).lower()])

kpis = [
    ("layers", "Total listings", f"{len(df)}"),
    ("sparkles", "Nuevos hoy", f"{len(nuevos_hoy)}"),
    ("star", "Score medio", f"{df['score'].mean():.1f}" if "score" in df.columns else "—"),
    ("wallet", "Precio medio", f"{df['price'].mean():,.0f} €" if "price" in df.columns else "—"),
    ("trending-down", "Bajadas", f"{len(bajadas)}"),
    ("waves", "Con piscina", f"{con_piscina}"),
]

kpi_cards = "".join(
    f"""<div class="kpi-card">
          <div class="kpi-icon">{icon(name, size=18)}</div>
          <div class="kpi-label">{label}</div>
          <div class="kpi-value">{value}</div>
        </div>"""
    for name, label, value in kpis
)
st.write("")
st.markdown(f'<div class="kpi-grid">{kpi_cards}</div>', unsafe_allow_html=True)
st.write("")

# ── Pestañas ─────────────────────────────────────────────────────

tab1, tab2, tab3, tab4 = st.tabs([
    "Listados completos",
    "Top scoring",
    "Evolución y análisis",
    "Bajadas de precio",
])

# ── TAB 1: Listados completos ────────────────────────────────────

with tab1:
    st.write("")
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        if "location" in df.columns:
            ubicaciones = sorted(df["location"].dropna().unique())
            filtro_ubi = st.multiselect("Ubicación", ubicaciones, default=[], key="f1_ubi")
        else:
            filtro_ubi = []
    with col_f2:
        score_range = st.slider("Rango de score", 0, 100, (0, 100), key="f1_score")
    with col_f3:
        if "price" in df.columns:
            pmin, pmax = int(df["price"].min()), int(df["price"].max())
            filtro_precio = st.slider("Rango de precio (€)", pmin, pmax, (pmin, pmax), key="f1_precio")
        else:
            filtro_precio = None

    df_filtrado = df.copy()
    if filtro_ubi and "location" in df.columns:
        df_filtrado = df_filtrado[df_filtrado["location"].isin(filtro_ubi)]
    if "score" in df.columns:
        df_filtrado = df_filtrado[(df_filtrado["score"] >= score_range[0]) & (df_filtrado["score"] <= score_range[1])]
    if filtro_precio and "price" in df.columns:
        df_filtrado = df_filtrado[(df_filtrado["price"] >= filtro_precio[0]) & (df_filtrado["price"] <= filtro_precio[1])]

    columnas_csv = [c for c in ["title", "price", "score", "eur_m2", "location", "m2", "rooms", "bathrooms", "floor", "year_built", "energy_rating", "source", "first_seen", "url"] if c in df_filtrado.columns]
    columnas_display = [c for c in ["title", "price", "score", "eur_m2", "m2", "location", "url"] if c in df_filtrado.columns]

    col_rename = {
        "title": "Título", "price": "Precio (€)", "score": "Score", "eur_m2": "€/m²",
        "m2": "m²", "location": "Ubicación", "url": "Ver",
    }

    df_tabla = df_filtrado[columnas_display].copy()
    if "score" in df_tabla.columns:
        df_tabla = df_tabla.sort_values("score", ascending=False)

    # Columna de posición dedicada: medalla para el podio, número para el resto.
    medallas = {0: "🥇  1º", 1: "🥈  2º", 2: "🥉  3º"}
    df_tabla.insert(0, "_pos", [medallas.get(i, f"{i + 1}") for i in range(len(df_tabla))])

    st.dataframe(
        df_tabla.rename(columns=col_rename),
        use_container_width=True,
        hide_index=True,
        column_config={
            "_pos": st.column_config.TextColumn("#", width="small"),
            "Ver": st.column_config.LinkColumn("Ver", display_text="Ver →"),
            "Precio (€)": st.column_config.NumberColumn("Precio (€)", format="€%,d"),
            "€/m²": st.column_config.NumberColumn("€/m²", format="€%,d"),
            "Score": st.column_config.ProgressColumn("Score", format="%.0f", min_value=0, max_value=100),
            "m²": st.column_config.NumberColumn("m²", format="%.0f"),
        },
    )

    st.caption(f"{len(df_filtrado)} listings mostrados")
    csv_data = df_filtrado[columnas_csv].to_csv(index=False).encode("utf-8")
    st.download_button("Descargar CSV", csv_data, f"listings_{hoy}.csv", "text/csv")

# ── TAB 2: Top scoring ───────────────────────────────────────────

with tab2:
    st.write("")
    top_n = st.slider("Mostrar top", 5, 30, 15, key="tab2_slider")

    for i, (_, row) in enumerate(df.head(top_n).iterrows()):
        score = row.get("score", 0) or 0
        features, penalties, _ = parse_score_details(row)
        color = score_color(score)

        titulo = clean(row.get("title", "Sin título")) or "Sin título"
        url = row.get("url", "")
        link_open = f'<a class="prop-title" href="{url}" target="_blank">' if (isinstance(url, str) and url.startswith("http")) else '<span class="prop-title">'
        link_close = "</a>" if (isinstance(url, str) and url.startswith("http")) else "</span>"

        meta_fields = [
            ("map-pin", row.get("location", "—")),
            ("building", f"Planta {row.get('floor', '—')}"),
            ("calendar", row.get("year_built", "—")),
            ("zap", row.get("energy_rating", "—")),
        ]
        meta = "".join(
            f'<span class="meta-item">{icon(ic, size=15)}{clean(str(val)) or "—"}</span>'
            for ic, val in meta_fields
        )

        precio = row.get("price", 0) or 0
        eur_m2 = row.get("eur_m2", 0) or 0
        m2 = row.get("m2", 0) or 0
        rooms = row.get("rooms", 0) or 0
        baths = row.get("bathrooms", 0) or 0

        chips = "".join(f'<span class="chip">{c}</span>' for c in features) if features else ""
        warns = "".join(f'<span class="chip chip-warn">{p}</span>' for p in penalties) if penalties else ""

        st.markdown(
            f"""
            <div class="prop-card">
              <div style="display:flex; gap:1.25rem; align-items:flex-start;">
                <div class="score-badge" style="background:{color};">{score:.0f}</div>
                <div style="flex:1; min-width:0;">
                  <div><span class="prop-rank">{i+1}.</span> {link_open}{titulo}{link_close}</div>
                  <div class="prop-meta">{meta}</div>
                  <div class="score-bar-track"><div class="score-bar-fill" style="width:{min(score,100)}%; background:{color};"></div></div>
                </div>
                <div style="text-align:right; white-space:nowrap;">
                  <div style="font-size:1.15rem; font-weight:600; color:#18181b;">{precio:,.0f} €</div>
                  <div style="font-size:0.8rem; color:#71717a;">{eur_m2:,.0f} €/m²</div>
                  <div style="font-size:0.8rem; color:#a1a1aa; margin-top:0.3rem; display:flex; gap:0.7rem; justify-content:flex-end;">
                    <span class="meta-item">{icon("ruler", size=14)}{m2:.0f} m²</span>
                    <span class="meta-item">{icon("bed", size=14)}{rooms:.0f}</span>
                    <span class="meta-item">{icon("bath", size=14)}{baths:.0f}</span>
                  </div>
                </div>
              </div>
              <div style="margin-top:0.75rem;">{chips}{warns}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        desc = row.get("description", "")
        if desc and len(desc) > 20:
            with st.expander("Descripción"):
                st.write(clean(desc[:1500]))

# ── TAB 3: Evolución + Análisis ─────────────────────────────────

with tab3:
    st.write("")
    col_c1, col_c2 = st.columns(2)

    with col_c1:
        st.subheader("Evolución diaria")
        if "_archivo" in df.columns and len(df["_archivo"].unique()) > 1:
            diario = df.groupby("_archivo").agg(
                count=("title", "count"),
                avg_score=("score", "mean"),
                avg_price=("price", "mean"),
                min_price=("price", "min"),
                max_price=("price", "max"),
            ).reset_index().sort_values("_archivo")

            fig1 = go.Figure()
            fig1.add_trace(go.Bar(x=diario["_archivo"], y=diario["count"],
                                  name="Listings", marker_color=SUBTLE,
                                  marker_line_width=0))
            fig1.add_trace(go.Scatter(x=diario["_archivo"], y=diario["avg_score"],
                                      name="Score medio", yaxis="y2",
                                      line=dict(color=ACCENT, width=2.5)))
            style_fig(fig1, "Listings y score medio por día")
            fig1.update_layout(
                yaxis=dict(title=None),
                yaxis2=dict(title=None, overlaying="y", side="right", range=[0, 100], showgrid=False),
                legend=dict(x=0.01, y=0.99),
            )
            st.plotly_chart(fig1, use_container_width=True)

            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=diario["_archivo"], y=diario["avg_price"],
                                      mode="lines+markers", name="Medio",
                                      line=dict(color=ACCENT, width=2.5)))
            fig2.add_trace(go.Scatter(x=diario["_archivo"], y=diario["min_price"],
                                      mode="lines", name="Mínimo",
                                      line=dict(color=SUBTLE, width=1.5, dash="dot")))
            fig2.add_trace(go.Scatter(x=diario["_archivo"], y=diario["max_price"],
                                      mode="lines", name="Máximo",
                                      line=dict(color=SUBTLE, width=1.5, dash="dot")))
            style_fig(fig2, "Evolución de precios (€)")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Se necesitan al menos 2 días de datos para ver evolución.")

    with col_c2:
        st.subheader("Distribución de scores")
        if "score" in df.columns:
            fig3 = px.histogram(df, x="score", nbins=20, color_discrete_sequence=[ACCENT])
            style_fig(fig3)
            fig3.update_traces(marker_line_width=0, opacity=0.85)
            fig3.update_layout(xaxis_title="Score", yaxis_title=None, bargap=0.08)
            st.plotly_chart(fig3, use_container_width=True)

        st.subheader("Top ubicaciones")
        if "location" in df.columns:
            loc_counts = df["location"].value_counts().head(10).reset_index()
            loc_counts.columns = ["Ubicación", "Cantidad"]
            fig4 = px.bar(loc_counts, x="Cantidad", y="Ubicación", orientation="h",
                          color_discrete_sequence=[ACCENT])
            style_fig(fig4)
            fig4.update_traces(marker_line_width=0)
            fig4.update_layout(xaxis_title=None, yaxis_title=None,
                               yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig4, use_container_width=True)

# ── TAB 4: Bajadas de precio ─────────────────────────────────────

with tab4:
    st.write("")
    st.subheader("Listings con bajada de precio detectada")

    if not bajadas.empty:
        bajadas_show = bajadas.sort_values("price_drop", ascending=False)
        for _, row in bajadas_show.iterrows():
            titulo = clean(row.get("title", "Sin título")) or "Sin título"
            url = row.get("url", "")
            link_open = f'<a class="prop-title" href="{url}" target="_blank">' if (isinstance(url, str) and url.startswith("http")) else '<span class="prop-title">'
            link_close = "</a>" if (isinstance(url, str) and url.startswith("http")) else "</span>"
            meta = " · ".join(str(clean(p) or "—") for p in [row.get("location", "—"), row.get("source", "—")])

            prev = row.get("previous_price", 0) or 0
            cur = row.get("price", 0) or 0
            drop = row.get("price_drop", 0) or 0
            pct = (drop / prev * 100) if prev else 0

            st.markdown(
                f"""
                <div class="prop-card">
                  <div style="display:flex; gap:1.25rem; align-items:center;">
                    <div style="flex:1; min-width:0;">
                      <div>{link_open}{titulo}{link_close}</div>
                      <div class="prop-meta">{meta}</div>
                    </div>
                    <div style="text-align:right; white-space:nowrap;">
                      <div style="font-size:0.8rem; color:#a1a1aa; text-decoration:line-through;">{prev:,.0f} €</div>
                      <div style="font-size:1.15rem; font-weight:600; color:#18181b;">{cur:,.0f} €</div>
                    </div>
                    <div class="score-badge" style="background:#15803d; min-width:auto; padding:0 0.85rem; font-size:0.95rem;">
                      −{pct:.0f}%
                    </div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info("No se han detectado bajadas de precio todavía. Aparecerán aquí cuando un listing baje entre pasadas.")

# ── Footer ───────────────────────────────────────────────────────

st.write("")
st.divider()
st.caption(
    f"Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} · "
    f"Datos en `{DATA_DIR}` · [Forzar recarga](?rerun) · "
    f"Scraper: property_scorer.py (pisos.com · Madrid Sur + Toledo Norte · ≤ 250.000 €)"
)
