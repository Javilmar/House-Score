"""
Dashboard de Búsqueda de Vivienda — Madrid Sur + Toledo Norte
Hecho a medida del property_scorer.py (pisos.com scraping + scoring)

Lanzar: streamlit run app.py
"""

import re
import json
import math
import unicodedata
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
from datetime import date, datetime

st.set_page_config(
    page_title="House Score",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed",
)

DATA_DIR = Path(__file__).resolve().parent.parent / "datos"
ASSETS_DIR = Path(__file__).resolve().parent / "assets"

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

# ── Fiscalidad hipotecaria (tipos orientativos 2024-2026, editables) ──
# Segunda mano → ITP autonómico; Obra nueva → IVA 10% + AJD autonómico.
# Existen bonificaciones por edad, familia numerosa, VPO, etc. no reflejadas.
IVA_OBRA_NUEVA = 0.10
ITP = {"Comunidad de Madrid": 0.06, "Castilla-La Mancha": 0.09}
AJD = {"Comunidad de Madrid": 0.0075, "Castilla-La Mancha": 0.015}
OTROS_GASTOS_PCT = 0.015          # notaría + registro + gestoría (~1,5%)
TASACION_EUR = 400                 # tasación bancaria orientativa (€ fijos)
CCAA_DEFAULT = "Comunidad de Madrid"
HIP_DEFAULTS = {"entrada_pct": 0.20, "plazo": 30, "tin": 0.03}


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
        @import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300..600;1,9..144,300..500&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

        :root {
            --font-display: 'Fraunces', 'Times New Roman', serif;
            --font-sans: 'Inter', system-ui, -apple-system, sans-serif;
            --font-mono: 'JetBrains Mono', ui-monospace, monospace;
        }

        html, body, [class*="css"], .stMarkdown, .stMetric {
            font-family: var(--font-sans);
        }

        .stApp { background: #09090b; }
        .block-container { padding-top: 3rem; padding-bottom: 4rem; max-width: 1320px; }

        /* Títulos en Fraunces (display serif) — estilo Skilio */
        h1, h2, h3, h4 {
            font-family: var(--font-display) !important;
            font-weight: 400 !important;
            letter-spacing: -0.02em !important;
            line-height: 1.15 !important;
            color: #fafafa !important;
        }
        h2, h3 { color: #e4e4e7 !important; }

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
        .kpi-value { font-family: var(--font-display); font-size: 1.7rem; font-weight: 600;
                     color: #fafafa; margin-top: 0.1rem; letter-spacing: -0.01em; }

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

        /* Desglose de puntuación */
        .score-breakdown {
            margin-top: 0.85rem; border-top: 1px solid #27272a; padding-top: 0.65rem;
        }
        .score-breakdown > summary {
            cursor: pointer; font-size: 0.78rem; color: #71717a; font-weight: 500;
            list-style: revert; user-select: none;
        }
        .score-breakdown > summary:hover { color: #a1a1aa; }
        .sb-table { width: 100%; border-collapse: collapse; margin-top: 0.55rem; }
        .sb-row td { padding: 0.18rem 0.3rem; font-size: 0.78rem; color: #d4d4d8; vertical-align: top; }
        .sb-row td:last-child { text-align: right; white-space: nowrap; font-family: 'JetBrains Mono', monospace; min-width: 3.5rem; }
        .sb-pts-pos { color: #4ade80; font-weight: 600; }
        .sb-pts-neg { color: #f87171; font-weight: 600; }
        .sb-pts-zero { color: #52525b; font-weight: 500; }
        .sb-total td { padding-top: 0.4rem; border-top: 1px solid #3f3f46; font-weight: 700; color: #fafafa; font-size: 0.82rem; }
        .sb-total td:last-child { font-family: 'JetBrains Mono', monospace; }

        /* Botones */
        .stButton button, .stDownloadButton button {
            border-radius: 10px; border: 1px solid #27272a; font-weight: 500;
            background: #18181b; color: #e4e4e7;
            transition: all 200ms ease-in-out;
        }
        .stDownloadButton button:hover { border-color: #6366f1; color: #818cf8; }

        /* Divisores más sutiles */
        hr { border-color: #27272a !important; }

        /* Tabla de listados (HTML propio, título clicable) */
        .list-table-wrap {
            border: 1px solid #27272a; border-radius: 14px; overflow: hidden;
            background: #131316;
        }
        .list-table { width: 100%; border-collapse: collapse; font-size: 0.86rem; }
        .list-table thead th {
            text-align: left; font-size: 0.7rem; font-weight: 600; color: #71717a;
            text-transform: uppercase; letter-spacing: 0.04em;
            padding: 0.7rem 0.85rem; border-bottom: 1px solid #27272a;
            background: #18181b; white-space: nowrap;
        }
        .list-table tbody td {
            padding: 0.65rem 0.85rem; border-bottom: 1px solid #1f1f23;
            color: #d4d4d8; vertical-align: middle;
        }
        .list-table tbody tr:last-child td { border-bottom: none; }
        .list-table tbody tr { transition: background 140ms ease; }
        .list-table tbody tr:hover { background: #18181b; }

        .lt-pos { font-family: var(--font-mono); font-weight: 600; color: #71717a;
                  white-space: nowrap; font-size: 0.9rem; }
        /* El título ES el enlace — color de acento, subrayado al hover, cursor de mano */
        .lt-title a {
            color: #818cf8; text-decoration: none; font-weight: 500; cursor: pointer;
            border-bottom: 1px solid rgba(129,140,248,0.25);
            transition: all 140ms ease;
        }
        .lt-title a:hover { color: #a5b4fc; border-bottom-color: #a5b4fc; }
        .lt-title span { color: #a1a1aa; }
        .lt-num { font-family: var(--font-mono); font-size: 0.8rem; white-space: nowrap; color: #a1a1aa; }
        .lt-price { font-family: var(--font-mono); font-weight: 600; color: #fafafa;
                    white-space: nowrap; }
        .lt-score-wrap { display: flex; align-items: center; gap: 0.55rem; min-width: 96px; }
        .lt-score-num { font-family: var(--font-mono); font-weight: 600;
                        width: 24px; color: #e4e4e7; font-size: 0.82rem; }
        .lt-score-track { display: block; flex: 1; height: 5px; background: #27272a;
                          border-radius: 999px; overflow: hidden; min-width: 50px; }
        .lt-score-fill { display: block; height: 100%; border-radius: 999px; }

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


# ── Clasificación por zona (Madrid Sur / Toledo Norte) ───────────
# Best-effort: el scraper no guarda el municipio de origen, así que se
# infiere del texto del anuncio. Los pueblos toledanos son de la Sagra.

_MADRID_SUR = [
    "getafe", "leganes", "mostoles", "alcorcon", "fuenlabrada", "parla",
    "pinto", "valdemoro", "ciempozuelos", "humanes", "grinon",
    "navalcarnero", "torrejon de la calzada",
    "cubas de la sagra", "batres", "serranillos del valle",
    "moraleja de enmedio", "arroyomolinos",
]
_TOLEDO_NORTE = [
    "illescas", "yeles", "esquivias", "yuncos", "yuncler", "yunclillos",
    "cedillo", "el viso de san juan", "viso de san juan", "carranque",
    "ugena", "recas", "lominchar", "alameda de la sagra",
    "cabanas de la sagra", "villaluenga", "anover de tajo", "sesena",
    "casarrubios", "valmojado", "magan", "cobeja", "numancia", "pantoja",
    "chozas de canales", "bargas", "mocejon", "burguillos", "cobisa",
    "olias", "castilla la mancha", "la sagra", "sagra",
    "provincia de toledo", "toledo",
]


def _sin_acentos(s):
    s = unicodedata.normalize("NFKD", str(s))
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def zona(*textos):
    """Devuelve 'Madrid Sur', 'Toledo Norte' o '—' según el texto del anuncio."""
    blob = _sin_acentos(" ".join(t for t in textos if t))
    if any(m in blob for m in _MADRID_SUR):
        return "Madrid Sur"
    if any(t in blob for t in _TOLEDO_NORTE):
        return "Toledo Norte"
    return "—"


def zona_a_ccaa(z):
    """Traduce la zona de la app a nombre de CCAA (para tipos fiscales)."""
    if z == "Madrid Sur":
        return "Comunidad de Madrid"
    if z == "Toledo Norte":
        return "Castilla-La Mancha"
    return CCAA_DEFAULT


_OBRA_NUEVA_KW = [
    "obra nueva", "a estrenar", "nueva construccion", "primera ocupacion",
    "de obra nueva", "promocion de obra", "llave en mano", "recien construid",
    "vivienda nueva", "promocion nueva",
]


def tipo_vivienda(*textos):
    """'Obra nueva' si el anuncio lo indica; 'Segunda mano' en caso contrario."""
    blob = _sin_acentos(" ".join(t for t in textos if t))
    if any(kw in blob for kw in _OBRA_NUEVA_KW):
        return "Obra nueva"
    return "Segunda mano"


# Plantilla de la tabla interactiva (HTML + JS de ordenación en cliente).
# Marcadores __THEAD__ / __ROWS__ se sustituyen con .replace (no f-string,
# para no escapar las llaves de CSS/JS).
_TABLA_TEMPLATE = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap');
* { box-sizing: border-box; }
body { margin: 0; background: #09090b; font-family: 'Inter', sans-serif; }
.wrap { border: 1px solid #27272a; border-radius: 14px; overflow: hidden; background: #131316; }
table { width: 100%; border-collapse: collapse; font-size: 0.86rem; }
thead th {
  text-align: left; font-size: 0.7rem; font-weight: 600; color: #a1a1aa;
  text-transform: uppercase; letter-spacing: 0.04em; padding: 0.7rem 0.85rem;
  border-bottom: 1px solid #27272a; background: #18181b; white-space: nowrap;
  position: sticky; top: 0; cursor: pointer; user-select: none; z-index: 1;
}
thead th.noord { cursor: default; width: 34px; }
thead th:hover:not(.noord) { color: #fafafa; }
.arr { color: #818cf8; font-size: 0.78rem; }
tbody td { padding: 0.6rem 0.85rem; border-bottom: 1px solid #1f1f23; color: #d4d4d8; vertical-align: middle; }
tbody tr:last-child td { border-bottom: none; }
tbody tr:hover { background: #18181b; }
.lt-pos { font-family: 'JetBrains Mono', monospace; font-size: 0.95rem; white-space: nowrap; }
.lt-title a { color: #818cf8; text-decoration: none; font-weight: 500; border-bottom: 1px solid rgba(129,140,248,0.25); }
.lt-title a:hover { color: #a5b4fc; border-bottom-color: #a5b4fc; }
.lt-title span { color: #a1a1aa; }
.lt-num { font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; white-space: nowrap; color: #a1a1aa; }
.lt-price { font-family: 'JetBrains Mono', monospace; font-weight: 600; color: #fafafa; white-space: nowrap; }
.lt-score-wrap { display: flex; align-items: center; gap: 0.55rem; min-width: 96px; }
.lt-score-num { font-family: 'JetBrains Mono', monospace; font-weight: 600; width: 24px; color: #e4e4e7; font-size: 0.82rem; }
.lt-score-track { display: block; flex: 1; height: 5px; background: #27272a; border-radius: 999px; overflow: hidden; min-width: 50px; }
.lt-score-fill { display: block; height: 100%; border-radius: 999px; }
.lt-tag { font-size: 0.72rem; padding: 0.12rem 0.5rem; border-radius: 5px; white-space: nowrap; font-weight: 500; }
.lt-nuevo { background: rgba(34,197,94,0.12); color: #4ade80; border: 1px solid rgba(34,197,94,0.2); }
.lt-usada { background: rgba(255,255,255,0.04); color: #a1a1aa; border: 1px solid #27272a; }
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-thumb { background: #3f3f46; border-radius: 4px; }
.lt-goto-btn {
  background: rgba(99,102,241,0.08); border: 1px solid rgba(99,102,241,0.2);
  color: #818cf8; border-radius: 6px; padding: 0.22rem 0.45rem;
  cursor: pointer; font-size: 0.8rem; line-height: 1;
  transition: all 140ms ease;
}
.lt-goto-btn:hover { background: rgba(99,102,241,0.22); border-color: #818cf8; color: #a5b4fc; }
tbody td { vertical-align: top; }
.score-breakdown { margin-top: 0.45rem; }
.score-breakdown > summary { cursor: pointer; font-size: 0.7rem; color: #52525b; font-weight: 500; list-style: revert; user-select: none; }
.score-breakdown > summary:hover { color: #a1a1aa; }
.sb-table { width: 100%; border-collapse: collapse; margin-top: 0.35rem; min-width: 170px; }
.sb-row td { padding: 0.1rem 0.2rem; font-size: 0.7rem; color: #a1a1aa; }
.sb-total td { padding: 0.18rem 0.2rem; font-size: 0.72rem; font-weight: 600; color: #e4e4e7; border-top: 1px solid #27272a; }
.sb-pts-pos { color: #4ade80; font-family: 'JetBrains Mono', monospace; }
.sb-pts-neg { color: #f87171; font-family: 'JetBrains Mono', monospace; }
.sb-pts-zero { color: #52525b; font-family: 'JetBrains Mono', monospace; }
.sb-pts-neu { color: #a1a1aa; font-family: 'JetBrains Mono', monospace; }
</style></head><body>
<div class="wrap"><table id="lt"><thead>__THEAD__</thead><tbody>__ROWS__</tbody></table></div>
<script>
function goToHipoteca(precio, tipo_idx, ccaa_idx) {
  var p = window.parent;
  var tipos = ["Segunda mano", "Obra nueva"];
  var ccaas = ["Comunidad de Madrid", "Castilla-La Mancha"];
  var url = p.location.pathname
    + '?hip_precio=' + precio
    + '&hip_tipo=' + encodeURIComponent(tipos[tipo_idx])
    + '&hip_ccaa=' + encodeURIComponent(ccaas[ccaa_idx])
    + '&hip_nav_id=' + Date.now();
  // Marcar en sessionStorage el tab destino (indice 4 = Hipoteca).
  // Sobrevive el reload y es sincrono → el watcher lo lee en cuanto carga.
  p.sessionStorage.setItem('_sw_tab', '4');
  var s = p.document.createElement('script');
  s.textContent = 'window.location.href=' + JSON.stringify(url) + ';';
  p.document.body.appendChild(s);
}
function goToCard(rank) {
  var p = window.parent;
  var tabs = p.document.querySelectorAll('[data-baseweb="tab"]');
  if (tabs && tabs[1]) tabs[1].click();
  var tries = 0;
  function tryScroll() {
    var el = p.document.getElementById('card-' + rank);
    if (el) {
      el.scrollIntoView({behavior: 'smooth', block: 'start'});
      el.style.transition = 'box-shadow 300ms ease';
      el.style.boxShadow = '0 0 0 2px #818cf8';
      setTimeout(function() { el.style.boxShadow = ''; }, 1800);
    } else if (tries < 12) { tries++; setTimeout(tryScroll, 150); }
  }
  setTimeout(tryScroll, 280);
}
function ord(idx, th) {
  var t = document.getElementById('lt'), tb = t.tBodies[0];
  var rows = Array.prototype.slice.call(tb.rows);
  var asc = th.getAttribute('data-dir') !== 'asc';
  var hs = t.tHead.rows[0].cells;
  for (var k = 0; k < hs.length; k++) {
    hs[k].removeAttribute('data-dir');
    var s = hs[k].querySelector('.arr'); if (s) s.textContent = '';
  }
  rows.sort(function(a, b) {
    var x = a.cells[idx].getAttribute('data-v'), y = b.cells[idx].getAttribute('data-v');
    var nx = parseFloat(x), ny = parseFloat(y);
    var xn = (x !== '' && x != null && !isNaN(nx)), yn = (y !== '' && y != null && !isNaN(ny));
    var c;
    if (xn && yn) c = nx - ny;
    else if (xn) c = -1;
    else if (yn) c = 1;
    else c = ('' + x).localeCompare('' + y, 'es', { sensitivity: 'base' });
    return asc ? c : -c;
  });
  for (var i = 0; i < rows.length; i++) tb.appendChild(rows[i]);
  th.setAttribute('data-dir', asc ? 'asc' : 'desc');
  var sp = th.querySelector('.arr'); if (sp) sp.textContent = asc ? ' ▲' : ' ▼';
}
</script></body></html>"""


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


@st.cache_data
def cargar_geojson_municipios(mtime: float = 0.0):
    """Carga el GeoJSON de límites municipales. mtime invalida el caché cuando cambia el fichero."""
    path = ASSETS_DIR / "municipios_zona.geojson"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


@st.cache_data
def cargar_criminalidad(mtime: float = 0.0):
    """Carga la tasa de criminalidad por municipio. mtime invalida el caché cuando cambia el fichero."""
    path = ASSETS_DIR / "criminalidad.csv"
    if not path.exists():
        return pd.DataFrame()
    # Saltar líneas de comentario (#)
    df_c = pd.read_csv(path, comment="#")
    df_c["tasa_criminalidad"] = pd.to_numeric(df_c["tasa_criminalidad"], errors="coerce")
    return df_c


def score_color(score):
    for threshold, color in SCORE_SCALE:
        if score >= threshold:
            return color
    return SCORE_SCALE[-1][1]


# ── Plotly: plantilla limpia ─────────────────────────────────────

def style_fig(fig, title=None):
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color=INK, family="Fraunces")) if title else None,
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
        if "⚠️" in d or "🕸️" in d or "❓" in d:
            penalties.append(clean(d))
        elif any(e in d for e in ["🏊", "🚗", "📦", "🌿", "🏡", "🛗", "🌳", "🏗️", "🔧", "🚇", "🏢", "⚡", "📅"]):
            features.append(clean(d))
        elif "💰" in d or "📐" in d or "💎" in d or "📉" in d:
            bonuses.append(clean(d))
    return features, penalties, bonuses


# Nombres legibles para emojis de características (líneas del scorer que son solo "🏊 (+15)")
FEATURE_NAMES = {
    "🏊": "Piscina",
    "🚗": "Garaje",
    "📦": "Trastero",
    "🌿": "Terraza",
    "🏡": "Patio",
    "🛗": "Ascensor",
    "🌳": "Jardín",
}

_PTS_RE = re.compile(r'\s*\(([+-]?\d+)\s*(?:pts)?\)\s*$')
_CAP_RE = re.compile(r'características capadas:\s*(\d+)[→>](\d+)', re.IGNORECASE)


def breakdown_score_details(prop):
    """Parsea score_details en ítems {label, points, categoria} y reconcilia con el score final."""
    details = prop.get("score_details", [])
    score_final = int(prop.get("score", 0) or 0)
    items = []

    for d in details:
        if not isinstance(d, str):
            continue

        # Línea de tope de características: "(características capadas: 25→15)"
        cap_m = _CAP_RE.search(d)
        if cap_m:
            raw = int(cap_m.group(1))
            capped = int(cap_m.group(2))
            items.append({
                "label": f"Características (tope: {raw}→{capped})",
                "points": capped - raw,
                "categoria": "características",
            })
            continue

        # Extraer puntos del último paréntesis anclado al final
        m = _PTS_RE.search(d)
        if m:
            pts = int(m.group(1))
            label_raw = _PTS_RE.sub("", d).strip()
        else:
            pts = 0
            label_raw = d.strip()

        # Expandir etiquetas de características que son solo emoji ("🏊" → "🏊 Piscina")
        for emoji, name in FEATURE_NAMES.items():
            if label_raw.rstrip() == emoji:
                label_raw = f"{emoji} {name}"
                break

        # Clasificar categoría
        if "💎" in d or "❓" in d:
            cat = "valor"
        elif "📐" in d:
            cat = "tamaño"
        elif any(e in d for e in ["🏊", "🚗", "📦", "🌿", "🏡", "🛗", "🌳"]):
            cat = "características"
        elif any(e in d for e in ["🏗️", "🔧", "📅"]):
            cat = "estado"
        elif any(e in d for e in ["🚇", "🏢", "⚡"]):
            cat = "ubicación"
        elif "📉" in d or "💰" in d:
            cat = "mercado"
        elif "⚠️" in d or "🕸️" in d:
            cat = "penalización"
        else:
            cat = "otro"

        items.append({"label": label_raw, "points": pts, "categoria": cat})

    # Reconciliar con el score final acotado (clamped 0-100 por el scorer)
    suma = sum(it["points"] for it in items)
    if suma != score_final:
        ajuste = score_final - suma
        items.append({
            "label": "Ajuste (límite 0-100)",
            "points": ajuste,
            "categoria": "penalización" if ajuste < 0 else "otro",
        })

    return items, score_final


def _render_breakdown_html(items, score_final):
    """Construye el bloque HTML <details> con el desglose de puntuación."""
    filas = []
    for it in items:
        pts = it["points"]
        label = it["label"]
        if pts > 0:
            pts_html = f'<span class="sb-pts-pos">+{pts}</span>'
        elif pts < 0:
            pts_html = f'<span class="sb-pts-neg">{pts}</span>'
        else:
            pts_html = f'<span class="sb-pts-zero">0</span>'
        filas.append(f'<tr class="sb-row"><td>{label}</td><td>{pts_html}</td></tr>')

    filas_html = "".join(filas)
    return (
        '<details class="score-breakdown">'
        "<summary>Ver desglose de puntuación</summary>"
        '<table class="sb-table">'
        f"{filas_html}"
        f'<tr class="sb-total"><td>Total</td><td>{score_final}</td></tr>'
        "</table>"
        "</details>"
    )


# ── Cálculo hipotecario ──────────────────────────────────────────

def calc_impuestos(precio, es_obra_nueva, ccaa):
    """Devuelve los ítems de impuestos y el total para una compraventa.

    Obra nueva → IVA 10% + AJD autonómico.
    Segunda mano → ITP autonómico.
    Tipos orientativos 2024-2026; pueden existir bonificaciones no reflejadas.
    """
    items = []
    try:
        p = float(precio)
        if not (p > 0 and math.isfinite(p)):
            return {"items": [], "total": 0}
    except (TypeError, ValueError):
        return {"items": [], "total": 0}

    if es_obra_nueva:
        iva = round(p * IVA_OBRA_NUEVA)
        ajd_tipo = AJD.get(ccaa, AJD[CCAA_DEFAULT])
        ajd = round(p * ajd_tipo)
        items = [
            (f"IVA (10%)", iva),
            (f"AJD ({ajd_tipo*100:.2f}% — {ccaa})", ajd),
        ]
        total = iva + ajd
    else:
        itp_tipo = ITP.get(ccaa, ITP[CCAA_DEFAULT])
        itp = round(p * itp_tipo)
        items = [(f"ITP ({itp_tipo*100:.0f}% — {ccaa})", itp)]
        total = itp

    return {"items": items, "total": total}


def calc_hipoteca(precio, entrada_pct, plazo_anios, tin, es_obra_nueva, ccaa):
    """Calcula cuota mensual (sistema francés) y desglose de costes.

    Devuelve un dict con:
      principal, entrada, cuota_mensual, impuestos (dict), otros_gastos,
      ahorro_necesario, total_intereses, total_pagado.
    """
    try:
        p = float(precio)
        if not (p > 0 and math.isfinite(p)):
            raise ValueError
    except (TypeError, ValueError):
        return {
            "principal": 0, "entrada": 0, "cuota_mensual": 0,
            "impuestos": {"items": [], "total": 0},
            "otros_gastos": 0, "ahorro_necesario": 0,
            "total_intereses": 0, "total_pagado": 0,
        }

    entrada = round(p * entrada_pct)
    principal = round(p - entrada)
    n = int(plazo_anios) * 12
    r = tin / 12

    if r > 0 and n > 0:
        cuota = principal * r / (1 - (1 + r) ** (-n))
    elif n > 0:
        cuota = principal / n
    else:
        cuota = 0

    total_pagado_prestamo = cuota * n
    total_intereses = max(0, total_pagado_prestamo - principal)

    impuestos = calc_impuestos(p, es_obra_nueva, ccaa)
    otros_gastos = round(p * OTROS_GASTOS_PCT) + TASACION_EUR
    ahorro_necesario = entrada + impuestos["total"] + otros_gastos

    return {
        "principal": principal,
        "entrada": entrada,
        "cuota_mensual": round(cuota),
        "impuestos": impuestos,
        "otros_gastos": otros_gastos,
        "ahorro_necesario": ahorro_necesario,
        "total_intereses": round(total_intereses),
        "total_pagado": round(total_pagado_prestamo + entrada + impuestos["total"] + otros_gastos),
    }


def _render_hipoteca_inline_html(precio, es_obra_nueva, ccaa):
    """Bloque <details> con estimación hipotecaria usando supuestos por defecto."""
    h = calc_hipoteca(
        precio,
        HIP_DEFAULTS["entrada_pct"],
        HIP_DEFAULTS["plazo"],
        HIP_DEFAULTS["tin"],
        es_obra_nueva,
        ccaa,
    )
    if h["cuota_mensual"] == 0:
        return ""

    def _e(v):
        return f"{int(round(v)):,}".replace(",", ".") + " €"

    tipo_str = "Obra nueva" if es_obra_nueva else "2ª mano"
    summary = (
        f"hipoteca ~{_e(h['cuota_mensual'])}/mes "
        f"<span style='color:#52525b;font-size:0.68rem;'>"
        f"(80%, {HIP_DEFAULTS['plazo']} a., {HIP_DEFAULTS['tin']*100:.1f}%)</span>"
    )

    filas = [
        f'<tr class="sb-row"><td>Entrada (20%)</td><td class="sb-pts-neu">{_e(h["entrada"])}</td></tr>',
    ]
    for etiqueta, importe in h["impuestos"]["items"]:
        filas.append(
            f'<tr class="sb-row"><td>{etiqueta}</td><td class="sb-pts-neu">{_e(importe)}</td></tr>'
        )
    filas += [
        f'<tr class="sb-row"><td>Otros gastos (gestoría, notaría, tasación…)</td><td class="sb-pts-neu">{_e(h["otros_gastos"])}</td></tr>',
        f'<tr class="sb-total"><td>Ahorro necesario</td><td>{_e(h["ahorro_necesario"])}</td></tr>',
        f'<tr class="sb-row"><td style="color:#52525b;">Total pagado (préstamo + entrada + gastos)</td>'
        f'<td class="sb-pts-neu" style="color:#52525b;">{_e(h["total_pagado"])}</td></tr>',
    ]

    return (
        f'<details class="score-breakdown">'
        f"<summary>{summary}</summary>"
        f'<table class="sb-table">'
        f"{''.join(filas)}"
        f"</table>"
        f"</details>"
    )


# ── UI ───────────────────────────────────────────────────────────

inject_styles()

st.title("House Score")
st.caption("Madrid Sur · Toledo Norte — pisos.com · idealista · Scoring a medida · Hasta 300.000 €")

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
# Listings sin €/m² fiable (datos insuficientes): no entran en el score medio
if "datos_insuficientes" in df.columns:
    di_mask = df["datos_insuficientes"].fillna(False).astype(bool)
    sin_valorar = df[di_mask]
    fiables = df[~di_mask]
else:
    sin_valorar = pd.DataFrame()
    fiables = df
score_src = fiables if ("score" in fiables.columns and not fiables.empty) else df

kpis = [
    ("layers", "Total listings", f"{len(df)}"),
    ("sparkles", "Nuevos hoy", f"{len(nuevos_hoy)}"),
    ("star", "Score medio", f"{score_src['score'].mean():.1f}" if "score" in score_src.columns else "—"),
    ("wallet", "Precio medio", f"{df['price'].mean():,.0f} €" if "price" in df.columns else "—"),
    ("trending-down", "Bajadas", f"{len(bajadas)}"),
    ("ruler", "Sin valorar", f"{len(sin_valorar)}"),
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

# ── Precarga hipoteca desde query params (navegación desde la tabla) ──
# Usamos hip_nav_id (timestamp del cliente) para aplicar los params solo
# una vez por navegación: si el mismo id ya fue procesado, el usuario está
# interactuando con la pestaña y no sobreescribimos sus cambios.
_hip_qp = st.query_params
_hip_nav_id = _hip_qp.get("hip_nav_id", "")
if _hip_nav_id and st.session_state.get("_last_hip_nav_id") != _hip_nav_id:
    st.session_state["_last_hip_nav_id"] = _hip_nav_id
    try:
        st.session_state["hip_precio"] = int(_hip_qp["hip_precio"])
    except (KeyError, TypeError, ValueError):
        pass
    if "hip_tipo" in _hip_qp:
        st.session_state["hip_tipo"] = _hip_qp["hip_tipo"]
    if "hip_ccaa" in _hip_qp:
        st.session_state["hip_ccaa"] = _hip_qp["hip_ccaa"]

# ── Watcher de navegacion rapida (MutationObserver) ─────────────
# Dispara en cuanto los tabs aparecen en el DOM, sin polling.
# Lee sessionStorage._sw_tab que goToHipoteca grabo antes del reload.
components.html("""<script>
(function(){
  var p = window.parent;
  var idx = parseInt(p.sessionStorage.getItem('_sw_tab') || '', 10);
  if (isNaN(idx)) return;
  p.sessionStorage.removeItem('_sw_tab');
  function tryClick() {
    var t = p.document.querySelectorAll('[data-baseweb="tab"]');
    if (t && t.length > idx) { t[idx].click(); return true; }
    return false;
  }
  if (!tryClick()) {
    var obs = new MutationObserver(function(_, o) { if (tryClick()) o.disconnect(); });
    obs.observe(p.document.body, {childList: true, subtree: true});
    setTimeout(function() { obs.disconnect(); }, 4000);
  }
})();
</script>""", height=0)

# ── Pestañas ─────────────────────────────────────────────────────

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "Listados completos",
    "Top scoring",
    "Evolución y análisis",
    "Bajadas de precio",
    "Hipoteca",
    "Cómo funciona",
    "Mapa de seguridad",
])

# ── TAB 1: Listados completos ────────────────────────────────────

with tab1:
    st.write("")

    # Columnas derivadas para filtros combinables (zona + municipio)
    base = df.copy()
    _recs = base.to_dict("records")
    base["_zona"] = [zona(r.get("location", ""), r.get("title", ""), r.get("description", "")) for r in _recs]

    def _muni(r):
        m = r.get("municipio")
        if isinstance(m, str) and m.strip():
            return m.replace("_", " ").title()
        mm = re.search(r"\(([^)]+)\)", str(r.get("location") or ""))
        return mm.group(1).strip() if mm else "—"

    base["_municipio"] = [_muni(r) for r in _recs]

    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        zonas_disp = [z for z in ("Madrid Sur", "Toledo Norte") if z in set(base["_zona"])]
        filtro_zona = st.multiselect("Zona", zonas_disp, default=[], key="f1_zona")
    with col_f2:
        # El municipio se acota a la(s) zona(s) elegida(s) → filtros combinativos
        muni_pool = base[base["_zona"].isin(filtro_zona)] if filtro_zona else base
        municipios = sorted(m for m in muni_pool["_municipio"].dropna().unique() if m and m != "—")
        filtro_muni = st.multiselect("Municipio", municipios, default=[], key="f1_muni")
    with col_f3:
        score_range = st.slider("Rango de score", 0, 100, (0, 100), key="f1_score")
    with col_f4:
        if "price" in base.columns and base["price"].notna().any():
            pmin, pmax = int(base["price"].min()), int(base["price"].max())
            filtro_precio = st.slider("Rango de precio (€)", pmin, pmax, (pmin, pmax),
                                      step=1000, format="%,d €", key="f1_precio")
        else:
            filtro_precio = None

    df_filtrado = base.copy()
    if filtro_zona:
        df_filtrado = df_filtrado[df_filtrado["_zona"].isin(filtro_zona)]
    if filtro_muni:
        df_filtrado = df_filtrado[df_filtrado["_municipio"].isin(filtro_muni)]
    if "score" in df_filtrado.columns:
        df_filtrado = df_filtrado[(df_filtrado["score"] >= score_range[0]) & (df_filtrado["score"] <= score_range[1])]
    if filtro_precio and "price" in df_filtrado.columns:
        df_filtrado = df_filtrado[(df_filtrado["price"] >= filtro_precio[0]) & (df_filtrado["price"] <= filtro_precio[1])]

    columnas_csv = [c for c in ["title", "price", "score", "eur_m2", "location", "m2", "rooms", "bathrooms", "floor", "year_built", "energy_rating", "source", "first_seen", "url"] if c in df_filtrado.columns]

    df_tabla = df_filtrado.copy()
    if "score" in df_tabla.columns:
        df_tabla = df_tabla.sort_values("score", ascending=False)

    def _fmt_eur(v):
        try:
            f = float(v)
            if not math.isfinite(f):
                return "—"
            return f"{int(round(f)):,}".replace(",", ".") + " €"
        except (ValueError, TypeError):
            return "—"

    def _num(v):
        try:
            f = float(v)
            return f if math.isfinite(f) else ""
        except (ValueError, TypeError):
            return ""

    url_to_rank = {str(r.get("url", "")): i for i, (_, r) in enumerate(df.iterrows())}

    medallas = {0: "🥇", 1: "🥈", 2: "🥉"}
    filas = []
    for i, (_, row) in enumerate(df_tabla.iterrows()):
        pos = medallas.get(i, "")
        titulo = clean(row.get("title", "")) or "Sin título"
        url = row.get("url", "")
        if isinstance(url, str) and url.startswith("http"):
            titulo_html = f'<a href="{url}" target="_blank" rel="noopener">{titulo}</a>'
        else:
            titulo_html = f"<span>{titulo}</span>"
        di = row.get("datos_insuficientes")
        if pd.notna(di) and bool(di):
            titulo_html = ('<span class="lt-tag lt-usada" '
                           'title="Sin m² fiable: no valorado">s/valorar</span> ') + titulo_html

        sc = row.get("score", 0) or 0
        sc = sc if isinstance(sc, (int, float)) and math.isfinite(sc) else 0
        m2_val = row.get("m2")
        m2_txt = f"{int(m2_val)}" if pd.notna(m2_val) and math.isfinite(m2_val) else "—"
        ubi = zona(row.get("location", ""), row.get("title", ""), row.get("description", ""))
        feats = row.get("features", [])
        feats_txt = " ".join(feats) if isinstance(feats, list) else ""
        tipo = tipo_vivienda(row.get("title", ""), row.get("description", ""), feats_txt)
        tipo_cls = "lt-nuevo" if tipo == "Obra nueva" else "lt-usada"
        col = score_color(sc)

        bd_items, bd_total = breakdown_score_details(row)
        bd_html = _render_breakdown_html(bd_items, bd_total) if bd_items else ""

        ccaa_fila = zona_a_ccaa(ubi)
        es_obra_nueva_fila = (tipo == "Obra nueva")

        _precio_int = int(row.get("price") or 0)
        _tipo_idx = 1 if es_obra_nueva_fila else 0
        _ccaa_idx = 1 if ccaa_fila == "Castilla-La Mancha" else 0
        hip_btn = (
            f'<button class="lt-goto-btn" '
            f'onclick="goToHipoteca({_precio_int},{_tipo_idx},{_ccaa_idx})" '
            f'title="Calcular hipoteca" style="margin-top:0.3rem;">€</button>'
        )

        url_str = str(row.get("url", ""))
        global_rank = url_to_rank.get(url_str, -1)
        if global_rank >= 0 and global_rank < 30:
            goto_cell = (
                f'<td style="padding:0.4rem 0.5rem;">'
                f'<div style="display:flex;flex-direction:column;align-items:center;gap:0.2rem;">'
                f'<button class="lt-goto-btn" onclick="goToCard({global_rank})" title="Ver en Top scoring">↗</button>'
                f'{hip_btn}'
                f'</div></td>'
            )
        else:
            goto_cell = f'<td style="padding:0.4rem 0.5rem;text-align:center;">{hip_btn}</td>'

        filas.append(
            "<tr>"
            f'<td class="lt-pos">{pos}</td>'
            f'<td class="lt-title" data-v="{titulo.lower()}">{titulo_html}</td>'
            f'<td class="lt-price" data-v="{_num(row.get("price"))}">{_fmt_eur(row.get("price"))}</td>'
            f'<td data-v="{sc:.0f}"><div class="lt-score-wrap"><span class="lt-score-num">{sc:.0f}</span>'
            f'<span class="lt-score-track"><span class="lt-score-fill" '
            f'style="width:{min(sc, 100)}%;background:{col};"></span></span></div>{bd_html}</td>'
            f'<td class="lt-num" data-v="{_num(row.get("eur_m2"))}">{_fmt_eur(row.get("eur_m2"))}</td>'
            f'<td class="lt-num" data-v="{_num(row.get("m2"))}">{m2_txt}</td>'
            f'<td data-v="{tipo}"><span class="lt-tag {tipo_cls}">{tipo}</span></td>'
            f'<td data-v="{ubi}">{ubi}</td>'
            f'{goto_cell}'
            "</tr>"
        )

    if filas:
        thead = (
            "<tr>"
            '<th class="noord"></th>'
            '<th onclick="ord(1,this)">Título<span class="arr"></span></th>'
            '<th onclick="ord(2,this)">Precio<span class="arr"></span></th>'
            '<th onclick="ord(3,this)">Score<span class="arr"></span></th>'
            '<th onclick="ord(4,this)">€/m²<span class="arr"></span></th>'
            '<th onclick="ord(5,this)">m²<span class="arr"></span></th>'
            '<th onclick="ord(6,this)">Tipo<span class="arr"></span></th>'
            '<th onclick="ord(7,this)">Ubicación<span class="arr"></span></th>'
            '<th class="noord" style="width:38px;" title="Ver en Top scoring"></th>'
            "</tr>"
        )
        doc = _TABLA_TEMPLATE.replace("__THEAD__", thead).replace("__ROWS__", "".join(filas))
        altura = min(660, 64 + len(filas) * 41)
        components.html(doc, height=altura, scrolling=True)
    else:
        st.info("No hay listados con esos filtros.")

    st.caption(f"{len(df_filtrado)} listings · clic en una cabecera para ordenar · clic en el título para abrir el anuncio")
    csv_data = df_filtrado[columnas_csv].to_csv(index=False).encode("utf-8")
    st.download_button("Descargar CSV", csv_data, f"listings_{hoy}.csv", "text/csv")

# ── TAB 2: Top scoring ───────────────────────────────────────────

with tab2:
    st.write("")
    top_n = st.slider("Mostrar top", 5, 30, 15, key="tab2_slider")

    for i, (_, row) in enumerate(df.head(top_n).iterrows()):
        score = row.get("score", 0) or 0
        features, penalties, _ = parse_score_details(row)
        breakdown_items, _ = breakdown_score_details(row)
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
            <div class="prop-card" id="card-{i}" style="scroll-margin-top:80px;">
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
              {_render_breakdown_html(breakdown_items, int(score))}
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

# ── TAB 5: Hipoteca ──────────────────────────────────────────────

with tab5:
    st.write("")
    st.subheader("Calculadora de hipoteca")

    precio_medio = int(df["price"].median()) if "price" in df.columns and df["price"].notna().any() else 200000

    col_h1, col_h2, col_h3 = st.columns(3)
    with col_h1:
        hip_precio = st.number_input(
            "Precio de compra (€)", min_value=10_000, max_value=5_000_000,
            value=precio_medio, step=5_000, format="%d", key="hip_precio",
        )
        _precio_fmt = f"{int(hip_precio):,}".replace(",", ".")
        st.markdown(
            f'<div style="font-family:\'Fraunces\',serif;font-size:2.4rem;'
            f'font-weight:400;letter-spacing:-0.03em;color:#fafafa;'
            f'line-height:1;margin:-0.25rem 0 1rem 0;">'
            f'{_precio_fmt}'
            f'<span style="font-size:1.1rem;color:#a1a1aa;margin-left:0.3rem;">€</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
        hip_tipo = st.radio(
            "Tipo de vivienda", ["Segunda mano", "Obra nueva"],
            index=0, key="hip_tipo", horizontal=True,
        )
        hip_ccaa = st.radio(
            "Comunidad autónoma", ["Comunidad de Madrid", "Castilla-La Mancha"],
            index=0, key="hip_ccaa", horizontal=True,
        )
    with col_h2:
        hip_entrada_pct = st.slider(
            "Entrada (%)", min_value=5, max_value=50, value=20, step=1,
            format="%d%%", key="hip_entrada",
        )
        hip_plazo = st.slider(
            "Plazo (años)", min_value=5, max_value=40, value=30, step=1,
            key="hip_plazo",
        )
    with col_h3:
        hip_tin = st.slider(
            "Tipo de interés fijo (%)", min_value=0.5, max_value=8.0,
            value=3.0, step=0.05, format="%.2f%%", key="hip_tin",
        )

    hip_es_obra_nueva = (hip_tipo == "Obra nueva")
    hip_result = calc_hipoteca(
        hip_precio, hip_entrada_pct / 100, hip_plazo,
        hip_tin / 100, hip_es_obra_nueva, hip_ccaa,
    )

    def _hip_eur(v):
        return f"{int(round(v)):,}".replace(",", ".") + " €"

    hip_kpis = [
        ("wallet",        "Cuota mensual",        _hip_eur(hip_result["cuota_mensual"])),
        ("zap",           "Ahorro necesario",      _hip_eur(hip_result["ahorro_necesario"])),
        ("trending-down", "Total intereses",       _hip_eur(hip_result["total_intereses"])),
        ("building",      "Total desembolso",      _hip_eur(hip_result["total_pagado"])),
    ]
    hip_cards = "".join(
        f'<div class="kpi-card">'
        f'<div class="kpi-icon">{icon(n, size=18)}</div>'
        f'<div class="kpi-label">{lbl}</div>'
        f'<div class="kpi-value">{val}</div>'
        f'</div>'
        for n, lbl, val in hip_kpis
    )
    st.markdown(f'<div class="kpi-grid">{hip_cards}</div>', unsafe_allow_html=True)

    st.write("")
    st.markdown("**Desglose de ahorro necesario:**")

    imp = hip_result["impuestos"]
    tipo_txt = "Obra nueva (IVA + AJD)" if hip_es_obra_nueva else "Segunda mano (ITP)"
    imp_filas = "".join(
        f'<tr class="sb-row"><td>{et}</td>'
        f'<td style="font-family:\'JetBrains Mono\',monospace;color:#a1a1aa;">{_hip_eur(im)}</td></tr>'
        for et, im in imp["items"]
    )
    otros_filas = (
        f'<tr class="sb-row"><td>Otros gastos (gestoría, notaría, tasación…)</td>'
        f'<td style="font-family:\'JetBrains Mono\',monospace;color:#a1a1aa;">{_hip_eur(hip_result["otros_gastos"])}</td></tr>'
    )
    entrada_fila = (
        f'<tr class="sb-row"><td>Entrada ({hip_entrada_pct}%)</td>'
        f'<td style="font-family:\'JetBrains Mono\',monospace;color:#a1a1aa;">{_hip_eur(hip_result["entrada"])}</td></tr>'
    )
    total_fila = (
        f'<tr class="sb-total"><td>Ahorro necesario total</td>'
        f'<td>{_hip_eur(hip_result["ahorro_necesario"])}</td></tr>'
    )

    desglose_html = f"""
    <div style="max-width:520px;">
      <table class="sb-table" style="background:#131316;border:1px solid #27272a;
             border-radius:10px;overflow:hidden;margin-top:0.5rem;">
        <thead><tr style="background:#18181b;">
          <th style="padding:0.5rem 0.6rem;font-size:0.72rem;font-weight:600;
                     color:#a1a1aa;text-transform:uppercase;letter-spacing:0.04em;
                     text-align:left;">Concepto ({tipo_txt})</th>
          <th style="padding:0.5rem 0.6rem;font-size:0.72rem;font-weight:600;
                     color:#a1a1aa;text-transform:uppercase;letter-spacing:0.04em;
                     text-align:left;">Importe</th>
        </tr></thead>
        <tbody>{entrada_fila}{imp_filas}{otros_filas}{total_fila}</tbody>
      </table>
    </div>
    """
    st.markdown(desglose_html, unsafe_allow_html=True)

    st.caption(
        "Tipos impositivos orientativos 2024-2026. ITP: C. Madrid 6% / CLM 9%. "
        "AJD (obra nueva): C. Madrid 0,75% / CLM 1,5%. IVA obra nueva: 10%. "
        "Otros gastos (~1,5% + tasación 400€) son estimaciones. "
        "Pueden existir bonificaciones por edad, familia numerosa, VPO, etc."
    )

# ── TAB 6: Cómo funciona ─────────────────────────────────────────

with tab6:
    st.write("")
    st.markdown(
        """
        Cada anuncio recibe una **puntuación de 0 a 100**. Lo que más pesa es
        si está **barato para su zona**: su precio por m² comparado con la
        **media de su municipio**. A eso se suman tamaño, características (con
        tope), señales de mercado y penalizaciones. Cuanto más alta la nota,
        mejor oportunidad. Así se reparten los puntos:
        """
    )

    def _bloque(titulo, subtitulo, items):
        filas = "".join(
            f'<div style="display:flex; justify-content:space-between; gap:1rem; '
            f'padding:0.4rem 0; border-bottom:1px solid #1f1f23;">'
            f'<span style="color:#d4d4d8;">{concepto}</span>'
            f'<span style="color:{color}; font-weight:600; white-space:nowrap; '
            f'font-variant-numeric:tabular-nums;">{pts}</span></div>'
            for concepto, pts, color in items
        )
        return (
            f'<div class="prop-card" style="margin-bottom:0;">'
            f'<div style="font-weight:600; color:#fafafa; margin-bottom:0.1rem;">{titulo}</div>'
            f'<div style="font-size:0.8rem; color:#71717a; margin-bottom:0.6rem;">{subtitulo}</div>'
            f"{filas}</div>"
        )

    POS = "#22c55e"   # suma
    NEG = "#f87171"   # resta
    NEU = "#818cf8"   # base

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            _bloque("💎 Valor vs zona", "Lo que MÁS pesa · €/m² frente a la media de su municipio", [
                ("≈ 20% o más bajo la media (chollo)", "+40", POS),
                ("En la media de su zona", "≈ +20", NEU),
                ("≈ 20% o más por encima (caro)", "+0", NEG),
                ("Sin m² fiable → no se puede valorar", "fuera del Top", NEG),
            ]),
            unsafe_allow_html=True,
        )
        st.write("")
        st.markdown(
            _bloque("📐 Superficie", "Cuanto más grande, mejor", [
                ("≥ 140 m²", "+15", NEU),
                ("≥ 120 m²", "+12", NEU),
                ("≥ 100 m²", "+8", NEU),
                ("≥ 80 m²", "+5", NEU),
            ]),
            unsafe_allow_html=True,
        )
        st.write("")
        st.markdown(
            _bloque("📈 Señales de mercado", "Cómo se comporta el anuncio en el tiempo", [
                ("📉 Ha bajado de precio", "+1 a +5", POS),
                ("🕸️ Lleva > 45 días anunciado", "−3", NEG),
                ("🕸️ Lleva > 90 días anunciado", "−5", NEG),
            ]),
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            _bloque("✨ Características", "Detectadas en anuncio y ficha · el total se limita a +15", [
                ("🏊 Piscina", "+15", POS),
                ("🚗 Garaje", "+12", POS),
                ("📦 Trastero", "+10", POS),
                ("🌿 Terraza / 🏡 Patio", "+10", POS),
                ("🛗 Ascensor / 🌳 Jardín", "+5", POS),
                ("Tope del bloque (no se acumula sin fin)", "máx +15", NEU),
            ]),
            unsafe_allow_html=True,
        )
        st.write("")
        st.markdown(
            _bloque("➕ Extras (suman)", "Antigüedad, ubicación y calidad", [
                ("🏗️ Obra nueva / a estrenar", "+10", POS),
                ("🚇 Cerca de transporte público", "+8", POS),
                ("🔧 Reformado", "+5", POS),
                ("📅 Construido desde 2000", "+1 a +5", POS),
                ("🏢 Ático / última planta", "+3", POS),
                ("⚡ Eficiencia energética A/B/C", "+2", POS),
            ]),
            unsafe_allow_html=True,
        )
        st.write("")
        st.markdown(
            _bloque("⚠️ Penalizaciones (restan)", "Avisan de posibles problemas", [
                ("🚫 Ocupada / no admite visitas", "−30", NEG),
                ("📍 Zona conflictiva", "−3 a −20", NEG),
            ]),
            unsafe_allow_html=True,
        )

    st.write("")
    st.markdown("##### De dónde salen los datos")

    with st.expander("¿De qué portales vienen los anuncios?"):
        st.markdown(
            "Los datos proceden de **pisos.com** (scraping fiable) e **idealista** "
            "(best-effort: si su sistema anti-robot DataDome bloquea la pasada, "
            "esa búsqueda se omite sin interrumpir pisos.com). Cada anuncio lleva "
            "el campo **Source** indicando su origen. **Fotocasa** queda fuera "
            "por ahora (bloqueo consistente)."
        )
    with st.expander("¿Qué municipios se rastrean?"):
        st.markdown(
            "Nos centramos en municipios a **30–40 min de Madrid por autovía** "
            "(corredores A-42, A-4 y A-5). **Toledo capital queda fuera**: "
            "está a ~55 min y es un mercado distinto."
        )
        c_ms, c_tn = st.columns(2)
        with c_ms:
            st.markdown(
                "**Madrid Sur (18)**\n\n"
                "Alcorcón · Arroyomolinos · Batres · Ciempozuelos · "
                "Cubas de la Sagra · Fuenlabrada · Getafe · Griñón · "
                "Humanes de Madrid · Leganés · Móstoles · Moraleja de Enmedio · "
                "Navalcarnero · Parla · Pinto · Serranillos del Valle · "
                "Torrejón de la Calzada · Valdemoro"
            )
        with c_tn:
            st.markdown(
                "**Toledo Norte (29)**\n\n"
                "Alameda de la Sagra · Añover de Tajo · Bargas · "
                "Burguillos de Toledo · Cabañas de la Sagra · Carranque · "
                "Casarrubios del Monte · Cedillo del Condado · Cobeja · Cobisa · "
                "Chozas de Canales · El Viso de San Juan · Esquivias · "
                "Illescas · Lominchar · Magán · Mocejón · Numancia de la Sagra · "
                "Olías del Rey · Pantoja · Recas · Seseña · Ugena · Valmojado · "
                "Villaluenga de la Sagra · Yeles · Yuncler · Yunclillos · Yuncos"
            )
    with st.expander("¿Cómo se asegura que el precio es real?"):
        st.markdown(
            'El listado de búsqueda a veces muestra precios "desde", que engañan. '
            "Por eso el sistema puntúa primero todos los anuncios, **visita la ficha "
            "completa de los mejores** y vuelve a puntuarlos con los datos reales: "
            "precio, metros, habitaciones, baños, año y estado de conservación. "
            "Por eso algún anuncio puede aparecer algo por encima de 300.000 €: su "
            "precio real (de la ficha) subió respecto al del listado, pero si su €/m² "
            "es bueno se mantiene como oportunidad."
        )
    with st.expander('¿Qué significa "barato para su zona"?'):
        st.markdown(
            "Es el factor que más pesa. Cada pasada calcula la **mediana de €/m² "
            "de cada municipio** a partir de todos los anuncios recogidos, y compara "
            "el €/m² de cada vivienda con esa media: si está por debajo, es un chollo "
            "y sube; si está por encima, baja. Si un municipio tiene pocos anuncios, "
            "se usa la media de su **zona** (Madrid Sur / Toledo Norte). "
            "**Matiz**: la media se calcula sobre anuncios de hasta 300.000 €, así que "
            "es la referencia del *segmento asequible*, no del mercado completo."
        )
    with st.expander('¿Por qué algunos salen como "sin valorar"?'):
        st.markdown(
            'Si un anuncio no trae los **m² de forma fiable** (faltan o el dato es '
            'absurdo), no se puede calcular su €/m² ni compararlo con su zona. Esos '
            'anuncios se marcan **"s/valorar"**, quedan **fuera del Top** y no cuentan '
            'en el "Score medio", pero siguen guardados por si quieres revisarlos.'
        )
    with st.expander("¿De dónde vienen los datos de peligrosidad del mapa?"):
        st.markdown(
            "El mapa de seguridad usa la **tasa de criminalidad oficial** (infracciones "
            "penales × 100 000 hab) publicada por el **Portal Estadístico de Criminalidad** "
            "del Ministerio del Interior. Solo tienen publicación oficial los municipios "
            "con más de **20 000 habitantes**, por lo que los pueblos pequeños de la Sagra "
            "toledana aparecen en gris. La tasa se calcula anualizado datos de Q1 2026. "
            "Fuente: estadisticasdecriminalidad.ses.mir.es"
        )

    st.caption("La puntuación es orientativa: ayuda a priorizar, no sustituye una visita.")

# ── TAB 7: Mapa de seguridad ──────────────────────────────────────

with tab7:
    st.write("")

    _gj_path = ASSETS_DIR / "municipios_zona.geojson"
    _csv_path = ASSETS_DIR / "criminalidad.csv"
    geojson_mun = cargar_geojson_municipios(_gj_path.stat().st_mtime if _gj_path.exists() else 0.0)
    df_crim = cargar_criminalidad(_csv_path.stat().st_mtime if _csv_path.exists() else 0.0)

    if geojson_mun is None or df_crim.empty:
        st.warning(
            "Activos del mapa no encontrados. Ejecuta primero el script de build:\n\n"
            "```\ncd house-dashboard/dashboard\npython scripts/build_mapa_assets.py\n```"
        )
    else:
        import plotly.express as px

        periodo = df_crim["periodo"].iloc[0] if "periodo" in df_crim.columns else "Q1 2026"
        tasa_max = df_crim["tasa_criminalidad"].max()
        tasa_min = df_crim["tasa_criminalidad"].min()

        # Escala de color: verde (seguro) → rojo (peligroso)
        COLOR_SCALE = [
            [0.0,  "#22c55e"],   # verde
            [0.35, "#84cc16"],
            [0.55, "#eab308"],   # amarillo
            [0.75, "#f97316"],   # naranja
            [1.0,  "#ef4444"],   # rojo
        ]

        fig_mapa = px.choropleth_map(
            df_crim,
            geojson=geojson_mun,
            locations="cod_ine",
            featureidkey="properties.cod_ine",
            color="tasa_criminalidad",
            color_continuous_scale=COLOR_SCALE,
            range_color=(tasa_min * 0.85, tasa_max * 1.05),
            hover_name="municipio",
            hover_data={
                "cod_ine": False,
                "tasa_criminalidad": ":.0f",
                "periodo": True,
            },
            labels={
                "tasa_criminalidad": "Tasa / 100 000 hab",
                "periodo": "Período",
            },
            center={"lat": 40.18, "lon": -3.78},
            zoom=9,
            map_style="carto-darkmatter",
            opacity=0.75,
        )

        fig_mapa.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=0, b=0),
            height=540,
            font=dict(family="Inter", size=12, color=MUTED),
            coloraxis_colorbar=dict(
                title="Tasa<br>/ 100k",
                tickfont=dict(color=MUTED, size=11),
                title_font=dict(color=MUTED, size=12),
                bgcolor=SURFACE,
                bordercolor=BORDER,
                thickness=14,
                len=0.65,
            ),
            hoverlabel=dict(
                bgcolor=SURFACE, bordercolor=BORDER,
                font=dict(family="Inter", color=INK),
            ),
        )

        st.plotly_chart(fig_mapa, use_container_width=True)

        # Municipios sin dato: los del GeoJSON que no están en df_crim
        crim_codes = set(df_crim["cod_ine"].astype(str))
        geo_codes = {f["properties"]["cod_ine"] for f in geojson_mun["features"]}
        sin_dato = sorted(
            f["properties"]["nombre"]
            for f in geojson_mun["features"]
            if f["properties"]["cod_ine"] not in crim_codes
        )

        st.caption(
            f"**Fuente**: Portal Estadístico de Criminalidad · Ministerio del Interior · "
            f"**Período**: {periodo} · "
            f"**Métrica**: infracciones penales / 100 000 hab · "
            f"**Rojo** = más peligroso · **Verde** = más seguro · "
            f"**Gris** = sin publicación oficial (<20 000 hab)"
        )

        with st.expander(f"Municipios sin datos oficiales ({len(sin_dato)} en gris)"):
            st.write(", ".join(sin_dato) if sin_dato else "Todos tienen datos.")

        st.write("")
        st.subheader("Ranking de peligrosidad")
        df_rank = df_crim[["municipio", "tasa_criminalidad"]].sort_values(
            "tasa_criminalidad", ascending=False
        ).reset_index(drop=True)
        df_rank.index += 1
        df_rank.columns = ["Municipio", "Tasa / 100 000 hab"]
        df_rank["Tasa / 100 000 hab"] = df_rank["Tasa / 100 000 hab"].map("{:.0f}".format)
        st.dataframe(df_rank, use_container_width=True, hide_index=False)

# ── Footer ───────────────────────────────────────────────────────

st.write("")
st.divider()
st.caption(
    f"Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} · "
    f"Datos en `{DATA_DIR}` · [Forzar recarga](?rerun) · "
    f"Scraper: property_scorer.py (pisos.com + idealista · Madrid Sur + Toledo Norte · ≤ 300.000 €)"
)
