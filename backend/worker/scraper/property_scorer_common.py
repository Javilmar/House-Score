#!/usr/bin/env python3
"""
property_scorer_common.py — Funciones comunes para los 3 lotes del scraper de propiedades.
"""

import asyncio
import json
import os
import re
import statistics
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import Optional

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from playwright_stealth import Stealth


# ─── CONFIGURACIÓN ────────────────────────────────────────────

DATA_DIR = Path(os.environ.get("HERMES_DATA_DIR", Path.home() / "AppData/Local/hermes"))
JSON_OUTPUT = DATA_DIR / "last_property_data.json"
IDEALISTA_SESSION = DATA_DIR / "idealista_session.json"

MAX_PRICE = 300_000

# Municipios Madrid Sur
MADRID_SUR = [
    "getafe", "leganes", "mostoles", "alcorcon",
    "fuenlabrada", "parla", "pinto", "valdemoro",
    "ciempozuelos", "humanes_de_madrid", "grinon",
    "navalcarnero", "torrejon_de_la_calzada",
    "cubas_de_la_sagra", "batres", "serranillos_del_valle",
    "moraleja_de_enmedio", "arroyomolinos",
]

# Toledo Norte
TOLEDO_NORTE = [
    "illescas",
    "sesena",
    "yeles",
    "ugena",
    "esquivias",
]

ALL_MUNICIPALITIES = MADRID_SUR + TOLEDO_NORTE
PROPERTY_TYPES = ["piso", "casa"]

BAD_ZONES = {
    "las margaritas": -15, "juan de la cierva": -8,
    "san isidro": -5, "sector iii": -5, "sector 3": -5,
    "la fortuna": -12, "zarzaquemada": -5,
    "parque vosa": -10, "echegaray": -10, "cuartel huertas": -8,
    "la avanzada": -12, "la cueva": -10, "el naranjo": -8, "la serna": -8,
    "la cantueña": -20, "la cantuena": -20, "parla este": -15,
    "las américas": -8, "las americas": -8,
    "el quiñón": -3, "el quinon": -3,
}

TRANSPORT_KEYWORDS = [
    "metro", "cercanías", "cercanias", "renfe",
    "transporte público", "transporte publico",
    "estación de tren", "estacion de tren",
    "parada de autobús", "parada de autobus",
    "bus", "autobús", "autobus",
    "bien comunicado", "conectado",
    "metro sur", "metrosur", "metroligero",
]

FEATURE_KEYWORDS = {
    "piscina": "🏊 Piscina",
    "garaje": "🚗 Garaje",
    "trastero": "📦 Trastero",
    "terraza": "🌿 Terraza",
    "patio": "🏡 Patio",
    "ascensor": "🛗 Ascensor",
    "jardín": "🌳 Jardín",
    "jardin": "🌳 Jardín",
}

REFERENCE_FILE = Path.home() / "house-dashboard" / "frontend" / "config" / "precios_referencia.json"
MIN_SAMPLE = 5
SANE_EUR_M2 = (200, 20000)
RANCIO_DIAS = (45, 90)

HAB_MIN = 2
SIZE_MIN = 70
EXTERIOR_OBLIGATORIO = False
EXTERIOR_PENALTY = -25
VALOR_CAP = 25

ZONA = {**{m: "madrid_sur" for m in MADRID_SUR},
        **{m: "toledo_norte" for m in TOLEDO_NORTE}}

PROVINCIA = {**{m: "madrid" for m in MADRID_SUR},
             **{m: "toledo" for m in TOLEDO_NORTE}}

IDEALISTA_SLUG = {
    "humanes_de_madrid": "humanes-de-madrid",
    "grinon": "grinon",
    "torrejon_de_la_calzada": "torrejon-de-la-calzada",
    "sesena": "sesena",
    "alcorcon": "alcorcon",
    "leganes": "leganes",
    "mostoles": "mostoles",
}

FOTOCASA_SLUG = {
    "humanes_de_madrid": "humanes-de-madrid",
    "torrejon_de_la_calzada": "torrejon-de-la-calzada",
    "cubas_de_la_sagra": "cubas-de-la-sagra",
    "serranillos_del_valle": "serranillos-del-valle",
    "moraleja_de_enmedio": "moraleja-de-enmedio",
    "navalcarnero": "navalcarnero",
    "grinon": "grinon",
    "sesena": "sesena",
}

EXTERIOR_KEYWORDS = ["terraza", "patio", "jardin", "jardín", "balcon", "balcón", "balcones"]

FEATURES = [
    (["piscina"], 8, "🏊 Piscina"),
    (["garaje", "garage"], 10, "🚗 Garaje"),
    (["trastero"], 6, "📦 Trastero"),
    (["ascensor"], 5, "🛗 Ascensor"),
]
FEATURES_CAP = 18

_NEG_RE = re.compile(r"\b(?:sin|no)\s+(?:\w+\s+){0,2}$")


def municipio_from_url(url: str) -> str:
    m = re.search(r"/venta/(?:piso|casa)-([a-z_]+)", url or "")
    return m.group(1) if m else ""


def eur_m2_of(price, size):
    if price and size and size > 0:
        v = price / size
        if SANE_EUR_M2[0] <= v <= SANE_EUR_M2[1]:
            return round(v)
    return None


def build_reference(samples, today_str):
    by_muni, by_zona = defaultdict(list), defaultdict(list)
    for muni, val in samples:
        by_muni[muni].append(val)
        z = ZONA.get(muni)
        if z:
            by_zona[z].append(val)
    return {
        "updated": today_str,
        "source": "median_own",
        "municipios": {m: {"eur_m2": round(statistics.median(v)), "n": len(v)}
                       for m, v in by_muni.items()},
        "zonas": {z: {"eur_m2": round(statistics.median(v)), "n": len(v)}
                  for z, v in by_zona.items()},
    }


def reference_eur_m2(reference, municipio):
    if not reference:
        return None
    muni = reference.get("municipios", {}).get(municipio)
    if muni and muni.get("n", 0) >= MIN_SAMPLE:
        return muni["eur_m2"]
    z = reference.get("zonas", {}).get(ZONA.get(municipio))
    if z:
        return z["eur_m2"]
    return muni["eur_m2"] if muni else None


def load_history(data_dir: Path, today_str: str) -> dict:
    hist = {}
    if not data_dir.exists():
        return hist
    for f in sorted(data_dir.glob("*.json")):
        if f.stem == today_str:
            continue
        try:
            for p in json.loads(f.read_text(encoding="utf-8")):
                url = p.get("url")
                if not url:
                    continue
                fs = p.get("first_seen") or f.stem
                prev = hist.get(url)
                if not prev or fs < prev["first_seen"]:
                    hist[url] = {"first_seen": fs, "price": p.get("price")}
                else:
                    prev["price"] = p.get("price")
        except Exception:
            continue
    return hist


def assign_market_fields(prop, history, today_str):
    prop["last_seen"] = today_str
    h = history.get(prop.get("url", ""))
    if h:
        prop["first_seen"] = h.get("first_seen", today_str)
        old, new = h.get("price"), prop.get("price")
        if old and new and new < old:
            prop["price_drop"] = old - new
            prop["previous_price"] = old
    else:
        prop.setdefault("first_seen", today_str)
    return prop


def _text_has_feature(feat: str, text: str) -> bool:
    for m in re.finditer(re.escape(feat), text):
        if _NEG_RE.search(text[max(0, m.start() - 20):m.start()]):
            continue
        return True
    return False


def _days_since(date_str, today):
    try:
        d = datetime.fromisoformat(str(date_str)[:10]).date()
        return max(0, (today - d).days)
    except Exception:
        return 0


def score_property(prop: dict, reference: dict = None, today: date = None) -> dict:
    if today is None:
        today = date.today()
    score = 0
    details = []
    cumple_requisitos = True

    price = prop.get("price", 0)
    size = prop.get("size_m2", 0)
    municipio = prop.get("municipio") or municipio_from_url(
        prop.get("source_url", "") or prop.get("url", ""))
    prop["municipio"] = municipio

    all_text = " ".join([
        prop.get("title", ""),
        prop.get("location", ""),
        prop.get("description", ""),
        " ".join(prop.get("features", [])),
        prop.get("conservation", ""),
    ]).lower()

    eur_m2 = eur_m2_of(price, size)
    prop["eur_m2"] = eur_m2 or 0
    ref = reference_eur_m2(reference, municipio)
    datos_insuficientes = eur_m2 is None or ref is None
    prop["datos_insuficientes"] = datos_insuficientes
    if not datos_insuficientes:
        desv = (ref - eur_m2) / ref
        pts = max(0, min(VALOR_CAP, round(VALOR_CAP * (desv + 0.20) / 0.40)))
        score += pts
        signo = "-" if desv >= 0 else "+"
        details.append(
            f"💎 {signo}{abs(desv)*100:.0f}% vs media {municipio or '?'} "
            f"({eur_m2:,}€/m² · ref {ref:,}) (+{pts})")
    else:
        details.append("❓ Datos insuficientes para valorar (sin m²/referencia fiable)")

    if size > 0 and SIZE_MIN > 0 and size < SIZE_MIN:
        cumple_requisitos = False
        details.append(f"📐 {size}m² < {SIZE_MIN}m² mínimo (no cumple)")
    elif size >= 140:
        score += 15; details.append(f"📐 Muy amplio: {size}m² (+15)")
    elif size >= 120:
        score += 12; details.append(f"📐 Amplio: {size}m² (+12)")
    elif size >= 100:
        score += 8; details.append(f"📐 Buen tamaño: {size}m² (+8)")
    elif size >= 80:
        score += 5; details.append(f"📐 Tamaño mínimo: {size}m² (+5)")
    elif size >= SIZE_MIN:
        score += 3; details.append(f"📐 Justo: {size}m² (+3)")
    elif size > 0:
        details.append(f"📐 Pequeño: {size}m² (0)")

    bedrooms = prop.get("bedrooms", 0) or 0
    if bedrooms > 0 and HAB_MIN > 0 and bedrooms < HAB_MIN:
        cumple_requisitos = False
        details.append(f"🛏️ {bedrooms} hab < {HAB_MIN} mínimo (no cumple)")
    elif bedrooms >= 3:
        score += 5; details.append(f"🛏️ {bedrooms} habitaciones (+5)")
    elif bedrooms == 2:
        score += 2; details.append(f"🛏️ {bedrooms} habitaciones (+2)")

    detail_features = prop.get("detail_features", {})
    exterior = (
        any(detail_features.get(k) for k in EXTERIOR_KEYWORDS) or
        any(_text_has_feature(k, all_text) for k in EXTERIOR_KEYWORDS)
    )
    prop["exterior"] = exterior
    if exterior:
        score += 12; details.append("🌿 Espacio exterior (+12)")
    else:
        score += EXTERIOR_PENALTY
        details.append(f"⚠️ Sin exterior detectado ({EXTERIOR_PENALTY} pts)")
        if EXTERIOR_OBLIGATORIO:
            cumple_requisitos = False

    feats = 0
    for variants, pts, emoji in FEATURES:
        present = any(detail_features.get(v) for v in variants) or \
                  any(_text_has_feature(v, all_text) for v in variants)
        if present:
            feats += pts
            details.append(f"{emoji} (+{pts})")
    if feats > FEATURES_CAP:
        details.append(f"   (características capadas: {feats}→{FEATURES_CAP})")
        feats = FEATURES_CAP
    score += feats

    if any(kw in all_text for kw in ["obra nueva", "a estrenar", "nueva construcción",
                                       "nueva construccion", "primera ocupación", "primera ocupacion"]):
        score += 10; details.append("🏗️ Obra nueva (+10)")
    elif any(kw in all_text for kw in ["reformado", "rehabilitado", "renovado", "reformada"]):
        score += 5; details.append("🔧 Reformado (+5)")

    year = prop.get("year_built", 0)
    if year >= 2020:
        score += 5; details.append(f"📅 Muy nuevo ({year}) (+5)")
    elif year >= 2010:
        score += 3; details.append(f"📅 Reciente ({year}) (+3)")
    elif year >= 2000:
        score += 1; details.append(f"📅 Moderado ({year}) (+1)")

    if any(kw in all_text for kw in TRANSPORT_KEYWORDS):
        score += 8; details.append("🚇 Cerca transporte público (+8)")

    if any(kw in all_text for kw in ["ático", "atico", "última planta", "ultima planta"]):
        score += 3; details.append("🏢 Ático (+3)")

    zone_text = f"{prop.get('location', '')} {prop.get('title', '')}".lower()
    for zone_name, penalty in BAD_ZONES.items():
        if zone_name in zone_text:
            score += penalty
            details.append(f"⚠️ Zona '{zone_name}' ({penalty} pts)")
            break

    energy = prop.get("energy_rating", "").upper()
    if energy in ("A", "B", "C"):
        score += 2; details.append(f"⚡ Eficiencia {energy} (+2)")

    if any(kw in all_text for kw in ["ocupado", "sin posesión", "sin posesion",
                                       "sin justo título", "sin justo titulo",
                                       "no admite visitas", "inmueble sin posesión"]):
        score -= 30
        details.append("⚠️ Propiedad ocupada / sin posesión (-30 pts)")

    drop = prop.get("price_drop", 0) or 0
    if drop > 0:
        prev = prop.get("previous_price") or (price + drop)
        pct = (drop / prev) if prev else 0
        pts = max(1, min(5, round(pct * 50)))
        score += pts
        details.append(f"📉 Bajó {drop:,}€ ({pct*100:.0f}%) (+{pts})")

    dias = _days_since(prop.get("first_seen"), today)
    if dias >= RANCIO_DIAS[1]:
        score -= 5; details.append(f"🕸️ {dias}d en el mercado (-5)")
    elif dias >= RANCIO_DIAS[0]:
        score -= 3; details.append(f"🕸️ {dias}d en el mercado (-3)")

    prop["cumple_requisitos"] = cumple_requisitos
    prop["score"] = max(0, min(100, score))
    prop["score_details"] = details
    return prop


# ─── DEDUPLICACIÓN ────────────────────────────────────────────

def load_seen_ids(max_age_days: int = 7) -> set:
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r") as f:
                data = json.load(f)
            now = datetime.now()
            ids = set()
            for entry in data.get("ids", []):
                if isinstance(entry, dict):
                    ts = entry.get("ts", "")
                    pid = entry.get("id", "")
                    if ts and pid:
                        try:
                            dt = datetime.fromisoformat(ts)
                            if (now - dt).days < max_age_days:
                                ids.add(pid)
                        except ValueError:
                            ids.add(pid)
                else:
                    ids.add(entry)
            return ids
        except Exception:
            return set()
    return set()


def save_seen_ids(ids: set, new_ids: set = None):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    existing = {}
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r") as f:
                data = json.load(f)
            for entry in data.get("ids", []):
                if isinstance(entry, dict) and entry.get("id"):
                    existing[entry["id"]] = entry.get("ts", datetime.now().isoformat())
                elif isinstance(entry, str):
                    existing[entry] = datetime.now().isoformat()
        except Exception:
            pass

    now = datetime.now().isoformat()
    for pid in ids:
        if pid not in existing:
            existing[pid] = now

    cutoff = (datetime.now() - timedelta(days=30)).isoformat()
    cleaned = {k: v for k, v in existing.items() if v >= cutoff}

    with open(STATE_FILE, "w") as f:
        json.dump({
            "ids": [{"id": k, "ts": v} for k, v in cleaned.items()],
            "updated": now
        }, f, indent=2)


STATE_FILE = DATA_DIR / "seen_properties.json"


# ─── PISOS.COM SCRAPERS ───────────────────────────────────────

async def scrape_search_page(page, url: str) -> list:
    try:
        await page.goto(url, timeout=20000, wait_until="domcontentloaded")
        await asyncio.sleep(2)
    except Exception as e:
        print(f"  ⚠️ Error cargando {url}: {e}", file=sys.stderr)
        return []

    try:
        link_data = await page.evaluate('''() => {
            const main = document.querySelector("main");
            if (!main) return [];
            const anchors = main.querySelectorAll('a[href*="comprar"]');
            return Array.from(anchors).map(a => ({
                href: a.href,
                text: a.innerText.substring(0, 150)
            }));
        }''')
    except Exception:
        link_data = []

    try:
        main_text = await page.evaluate('() => document.querySelector("main")?.innerText || ""')
    except Exception:
        main_text = ""

    listing_splits = re.split(r'\n(?=\d+/\d+\s)', main_text)
    text_blocks = [s.strip() for s in listing_splits if re.match(r'\d+/\d+', s.strip())]

    listings = []

    for i, block in enumerate(text_blocks):
        prop = {
            "source_url": url,
            "scraped_at": datetime.now().isoformat(),
        }

        lines = block.split("\n")
        clean = [l.strip() for l in lines if l.strip()]

        price = None
        for line in clean:
            m = re.search(r'([\d.]+)\s*€', line)
            if m:
                price = int(m.group(1).replace(".", ""))
                break

        if not price or price > MAX_PRICE:
            continue

        prop["price"] = price

        title = ""
        location = ""
        specs_data = {"habs": 0, "baños": 0, "m2": 0, "planta": ""}
        description_lines = []

        found_price = False
        found_title = False
        found_location = False
        in_description = False

        for line in clean:
            low = line.lower()

            if not found_price and "€" in line:
                found_price = True
                continue

            if found_price and not found_title and "calcula" in low:
                continue

            if found_price and not found_title and line in ("TOP", "NUEVO", "Oportunidad",
                                                             "Exclusivo", "Céntrico", "Centrico",
                                                             "Calidades superiores", "Con precio rebajado"):
                continue

            if found_price and not found_title and re.match(r'^[\d.]+\s*€\s*\(-\d+%\)', line):
                continue

            if found_price and not found_title and len(line) > 3:
                title = line
                found_title = True
                continue

            if found_title and not found_location:
                if "(" in line and ")" in line:
                    location = line
                    found_location = True
                    continue
                if not line:
                    continue

            if found_title and not in_description:
                if re.match(r'\d+\s*hab', low):
                    specs_data["habs"] = int(re.search(r'\d+', line).group())
                    continue
                if re.match(r'\d+\s*baño', low):
                    specs_data["baños"] = int(re.search(r'\d+', line).group())
                    continue
                if re.match(r'\d+\s*m²', low) or re.match(r'\d+\s*m2', low):
                    specs_data["m2"] = int(re.search(r'\d+', line).group())
                    continue
                if re.match(r'^(bajo|\d+ª\s*planta|ático|atico)$', low):
                    specs_data["planta"] = line
                    in_description = True
                    continue
                if specs_data["habs"] or specs_data["m2"]:
                    in_description = True

            if in_description:
                if "contactar" in low or "avísame" in low:
                    break
                if len(line) > 15:
                    description_lines.append(line)

        prop["title"] = title
        prop["location"] = location
        prop["size_m2"] = specs_data["m2"]
        prop["bedrooms"] = specs_data["habs"]
        prop["bathrooms"] = specs_data["baños"]
        prop["floor"] = specs_data["planta"]
        prop["description"] = " ".join(description_lines[:8])
        prop["features"] = []
        prop["detail_features"] = {}

        if i < len(link_data):
            prop["url"] = link_data[i]["href"]
            m = re.search(r'-(\d+_\d+)/?$', link_data[i]["href"])
            if m:
                prop["pisos_id"] = m.group(1)
            else:
                prop["pisos_id"] = link_data[i]["href"]
        else:
            prop["url"] = ""
            prop["pisos_id"] = ""

        listings.append(prop)

    return listings


async def scrape_detail_page(page, prop: dict) -> dict:
    url = prop.get("url", "")
    if not url:
        return prop

    try:
        await page.goto(url, timeout=20000, wait_until="domcontentloaded")
        await asyncio.sleep(0.5)
        try:
            cookie_btn = page.locator('button:has-text("Agree"), button:has-text("Aceptar"), button:has-text("Disagree and close")').first
            if await cookie_btn.is_visible(timeout=2000):
                await cookie_btn.click()
                await asyncio.sleep(0.3)
        except Exception:
            pass
    except Exception as e:
        return prop

    try:
        detail_text = await page.evaluate('() => document.querySelector("main")?.innerText || ""')
    except Exception:
        return prop

    if not detail_text:
        return prop

    detail_lower = detail_text.lower()

    price_match = re.search(r'(?:precio|desde)?\s*([\d.]+)\s*€', detail_text)
    if price_match:
        real_price = int(price_match.group(1).replace(".", ""))
        if real_price > 100:
            prop["price"] = real_price

    m2_match = re.search(r'superficie construida[:\s]*([\d.]+)\s*m', detail_lower)
    if not m2_match:
        m2_match = re.search(r'superficie útil[:\s]*([\d.]+)\s*m', detail_lower)
    if m2_match:
        prop["size_m2"] = int(m2_match.group(1).replace(".", ""))
    else:
        m2_match = re.search(r'([\d.]+)\s*m²', detail_text)
        if m2_match:
            prop["size_m2"] = int(m2_match.group(1).replace(".", ""))

    habs_match = re.search(r'(\d+)\s*hab', detail_lower)
    if habs_match:
        prop["bedrooms"] = int(habs_match.group(1))

    baths_match = re.search(r'(\d+)\s*baño', detail_lower)
    if baths_match:
        prop["bathrooms"] = int(baths_match.group(1))

    floor_match = re.search(r'(\d+ª)\s*planta|(bajo)', detail_lower)
    if floor_match:
        prop["floor"] = floor_match.group(0)

    floor_spec = re.search(r'(?:bajo|\d+ª\s*planta|ático|atico)', detail_lower)
    if floor_spec and not prop.get("floor"):
        prop["floor"] = floor_spec.group(0)

    seen_features = set()
    for feat in ["piscina", "garaje", "trastero", "terraza", "patio",
                 "ascensor", "jardín", "jardin", "balcón", "balcon",
                 "aire acondicionado", "calefacción", "calefaccion", "armario empotrado"]:
        if feat in detail_lower:
            seen_features.add(feat)

    features_section = False
    all_features = []

    for line in detail_text.split("\n"):
        line = line.strip()
        low = line.lower()

        if "características" in low:
            features_section = True
            continue
        if features_section:
            if "certificado energético" in low or "publicidad" in low:
                break
            if len(line) > 3:
                all_features.append(line)
                for feat in ["piscina", "garaje", "trastero", "terraza", "patio",
                             "ascensor", "jardín", "jardin", "balcón", "balcon",
                             "aire acondicionado"]:
                    if feat in low:
                        seen_features.add(feat)

    prop["features"] = all_features
    prop["detail_features"] = {f: True for f in seen_features}

    year_match = re.search(r'(?:construcción|construccion|construido|año|antigüedad)[:\s]*(\d{4})', detail_lower)
    if year_match:
        prop["year_built"] = int(year_match.group(1))
    else:
        ant_match = re.search(r'antigüedad:\s*(?:más de\s*)?(\d+)', detail_lower)
        if ant_match:
            prop["year_built"] = datetime.now().year - int(ant_match.group(1))
        else:
            prop["year_built"] = 0

    cons_match = re.search(r'conservaci[oó]n:\s*([^,\n]{3,50})', detail_lower)
    if not cons_match:
        cons_match = re.search(r'estado conservación:\s*([^,\n]{3,50})', detail_lower)
    if cons_match:
        prop["conservation"] = cons_match.group(1).strip()
    else:
        prop["conservation"] = ""

    energy_match = re.search(r'clasificaci[oó]n:\s*(\w)', detail_lower)
    if energy_match:
        rating = energy_match.group(1).upper()
        if rating in ("E",) and "en trámite" in detail_lower.lower():
            prop["energy_rating"] = ""
        elif rating in ("A", "B", "C", "D", "E", "F", "G"):
            prop["energy_rating"] = rating
        else:
            prop["energy_rating"] = ""

    update_match = re.search(r'(?:actualizado|publicado).*?(\d{2}/\d{2}/\d{4})', detail_lower)
    if update_match:
        prop["updated_date"] = update_match.group(1)

    desc_match = re.search(r'descripci[oó]n\s*\n(.+?)(?:\nmostrar|\ncaracter[ií]sticas)', detail_text, re.DOTALL | re.IGNORECASE)
    if desc_match:
        desc = desc_match.group(1).strip()
        desc = re.sub(r'(?:Español|Català|English|Deutsch|Français|Traducciones disponibles:).*?\n', '', desc)
        prop["description"] = desc[:2000]

    return prop


# ─── IDEALISTA SCRAPERS ───────────────────────────────────────

def _idealista_url(municipality: str) -> str:
    slug = IDEALISTA_SLUG.get(municipality, municipality.replace("_", "-"))
    provincia = PROVINCIA.get(municipality, "madrid")
    return f"https://www.idealista.com/venta-viviendas/{slug}-{provincia}/"


async def scrape_idealista_search(page, url: str) -> list:

    try:
        await page.goto(url, timeout=25000, wait_until="domcontentloaded")
        await asyncio.sleep(2.5)
    except Exception as e:
        print(f"  ⚠️ Error cargando {url}: {e}", file=sys.stderr)
        return []

    try:
        title = (await page.title()).lower()
        html_snippet = (await page.content())[:4000].lower()
    except Exception:
        title = ""
        html_snippet = ""

    block_signals = ["datadome", "captcha", "acceso restringido",
                     "are you a human", "robot", "access denied",
                     "403 forbidden", "please verify"]
    if any(sig in html_snippet or sig in title for sig in block_signals):
        raise BlockedError(f"idealista bloqueado en {url}")

    try:
        raw_listings = await page.evaluate(r'''() => {
            const items = document.querySelectorAll("article.item");
            return Array.from(items).map(art => {
                const link = art.querySelector("a.item-link");
                const href = link ? link.href : "";
                const title = link ? link.textContent.trim() : "";

                const priceEl = art.querySelector(".item-price");
                const priceText = priceEl ? priceEl.textContent.trim() : "";

                const details = Array.from(art.querySelectorAll(".item-detail"))
                    .map(el => el.textContent.trim());

                const descEl = art.querySelector(".item-description");
                const desc = descEl ? descEl.textContent.trim() : "";

                const locEl = art.querySelector(".item-detail-char:last-child, .item-location");
                const location = locEl ? locEl.textContent.trim() : "";

                const tagEl = art.querySelector(".item-flag");
                const tag = tagEl ? tagEl.textContent.trim() : "";

                return { href, title, priceText, details, desc, location, tag };
            });
        }''')
    except Exception as e:
        print(f"  ⚠️ Error evaluando JS idealista {url}: {e}", file=sys.stderr)
        return []

    listings = []
    for raw in raw_listings:
        href = raw.get("href", "")
        if not href:
            continue

        id_match = re.search(r'/inmueble/(\d+)/', href)
        uid = f"idealista:{id_match.group(1)}" if id_match else f"idealista:{href}"

        price_text = raw.get("priceText", "")
        price_m = re.search(r'([\d.]+)\s*€', price_text)
        if not price_m:
            continue
        price = int(price_m.group(1).replace(".", ""))
        if price > MAX_PRICE:
            continue

        size_m2 = 0
        bedrooms = 0
        bathrooms = 0
        floor = ""
        for det in raw.get("details", []):
            det_low = det.lower()
            m = re.search(r'([\d.]+)\s*m²', det_low)
            if m and not size_m2:
                size_m2 = int(m.group(1).replace(".", ""))
                continue
            m = re.search(r'(\d+)\s*hab', det_low)
            if m and not bedrooms:
                bedrooms = int(m.group(1))
                continue
            m = re.search(r'(\d+)\s*ba[ñn]', det_low)
            if m and not bathrooms:
                bathrooms = int(m.group(1))
                continue
            if re.search(r'(?:bajo|\d+ª?\s*planta|ático|planta baja)', det_low):
                floor = det

        listings.append({
            "source_url": url,
            "source": "idealista.com",
            "scraped_at": datetime.now().isoformat(),
            "uid": uid,
            "pisos_id": uid,
            "url": href,
            "title": raw.get("title", ""),
            "location": raw.get("location", "") or raw.get("desc", "")[:80],
            "price": price,
            "size_m2": size_m2,
            "bedrooms": bedrooms,
            "bathrooms": bathrooms,
            "floor": floor,
            "description": raw.get("desc", "")[:400],
            "features": [],
            "detail_features": {},
        })

    return listings


async def scrape_idealista_detail(page, prop: dict) -> dict:
    url = prop.get("url", "")
    if not url:
        return prop

    try:
        await page.goto(url, timeout=25000, wait_until="domcontentloaded")
        await asyncio.sleep(1.0)
    except Exception:
        return prop

    try:
        html_snippet = (await page.content())[:2000].lower()
        if any(s in html_snippet for s in ["datadome", "captcha", "access denied"]):
            return prop
        detail_text = await page.evaluate('() => document.querySelector("main")?.innerText || ""')
    except Exception:
        return prop

    if not detail_text:
        return prop

    detail_lower = detail_text.lower()

    price_m = re.search(r'([\d.]+)\s*€', detail_text)
    if price_m:
        real_price = int(price_m.group(1).replace(".", ""))
        if real_price > 100:
            prop["price"] = real_price

    m2_m = re.search(r'superficie construida[:\s]*([\d.]+)\s*m', detail_lower)
    if not m2_m:
        m2_m = re.search(r'superficie[:\s]*([\d.]+)\s*m', detail_lower)
    if m2_m:
        prop["size_m2"] = int(m2_m.group(1).replace(".", ""))

    h_m = re.search(r'(\d+)\s*hab', detail_lower)
    if h_m:
        prop["bedrooms"] = int(h_m.group(1))
    b_m = re.search(r'(\d+)\s*ba[ñn]', detail_lower)
    if b_m:
        prop["bathrooms"] = int(b_m.group(1))

    fl_m = re.search(r'(?:bajo|\d+ª\s*planta|ático)', detail_lower)
    if fl_m and not prop.get("floor"):
        prop["floor"] = fl_m.group(0)

    seen_features = set()
    for feat in ["piscina", "garaje", "trastero", "terraza", "patio",
                 "ascensor", "jardín", "jardin", "balcón", "balcon",
                 "aire acondicionado", "calefacción", "calefaccion", "armario empotrado"]:
        if feat in detail_lower:
            seen_features.add(feat)
    prop["detail_features"] = {f: True for f in seen_features}
    prop["features"] = list(seen_features)

    year_m = re.search(r'(?:construido|año construcción|antigüedad)[:\s]*(\d{4})', detail_lower)
    if year_m:
        prop["year_built"] = int(year_m.group(1))
    else:
        ant_m = re.search(r'antigüedad[:\s]*(?:más de\s*)?(\d+)', detail_lower)
        if ant_m:
            prop["year_built"] = datetime.now().year - int(ant_m.group(1))
        else:
            prop["year_built"] = 0

    cons_m = re.search(r'estado[:\s]*([^,\n]{3,50})', detail_lower)
    if cons_m:
        prop["conservation"] = cons_m.group(1).strip()

    energy_m = re.search(r'certificaci[oó]n energ[eé]tica[:\s]*([a-g])\b', detail_lower)
    if not energy_m:
        energy_m = re.search(r'clasificaci[oó]n[:\s]*([a-g])\b', detail_lower)
    if energy_m:
        rating = energy_m.group(1).upper()
        if rating in ("A", "B", "C", "D", "E", "F", "G"):
            prop["energy_rating"] = rating

    desc_m = re.search(r'descripci[oó]n\s*\n(.+?)(?:\ncaracter[ií]sticas|\nver más|\ncontactar)',
                       detail_text, re.DOTALL | re.IGNORECASE)
    if desc_m:
        prop["description"] = desc_m.group(1).strip()[:2000]

    return prop


# ─── FOTOCASA SCRAPERS ────────────────────────────────────────

def _fotocasa_url(municipality: str, page_num: int = 1) -> str:
    slug = FOTOCASA_SLUG.get(municipality, municipality.replace("_", "-"))
    base = f"https://www.fotocasa.es/es/comprar/viviendas/{slug}/todas-las-zonas/l"
    return base if page_num == 1 else f"{base}?sortType=score&page={page_num}"


async def scrape_fotocasa_search(page, url: str) -> list:

    try:
        await page.goto(url, timeout=30000, wait_until="domcontentloaded")
        await asyncio.sleep(1.5)
        prev_skeletons = None
        for _pass in range(8):
            for pct in (0.3, 0.6, 0.85, 1.0):
                await page.evaluate(f"window.scrollTo(0, document.body.scrollHeight * {pct})")
                await asyncio.sleep(0.5)
            skeletons = await page.evaluate(
                "() => Array.from(document.querySelectorAll('article'))"
                ".filter(a => a.innerHTML.includes('animate-pulse')).length"
            )
            if skeletons == 0:
                break
            if skeletons == prev_skeletons:
                break
            prev_skeletons = skeletons
        await page.evaluate("window.scrollTo(0, 0)")
        await asyncio.sleep(0.3)
    except Exception as e:
        print(f"  ⚠️ Error cargando {url}: {e}", file=sys.stderr)
        return []

    try:
        title = (await page.title()).lower()
        html_snippet = (await page.content())[:3000].lower()
    except Exception:
        title = html_snippet = ""

    block_signals = ["captcha", "acceso bloqueado", "uso indebido",
                     "access denied", "cloudflare", "403 forbidden"]
    if any(s in html_snippet or s in title for s in block_signals):
        raise BlockedError(f"fotocasa bloqueado en {url}")

    try:
        raw_listings = await page.evaluate(r"""() => {
            const cards = document.querySelectorAll('article');
            return Array.from(cards).map(card => {
                const allLinks = Array.from(card.querySelectorAll('a[href]'));
                const propLinks = allLinks.filter(a =>
                    /\/comprar\/vivienda\//.test(a.href) && /\/\d+\/d/.test(a.href)
                );
                if (propLinks.length === 0) return null;

                const href = propLinks[0].href.split('?')[0];

                const propTitleLinks = propLinks.filter(a => {
                    const t = a.innerText.trim();
                    return t.length > 15 && /^(piso|casa|chalet|ático|atico|estudio|local|dúplex|duplex|finca|villa|apartamento|bajo)/i.test(t);
                });
                const titleLink = propTitleLinks.length > 0
                    ? propTitleLinks.reduce((a, b) => a.innerText.length >= b.innerText.length ? a : b)
                    : propLinks[propLinks.length - 1];
                const title = titleLink ? titleLink.innerText.trim() : '';

                const text = card.innerText || '';
                return { href, title, text };
            }).filter(x => x && x.href);
        }""")
    except Exception as e:
        print(f"  ⚠️ Error evaluando JS fotocasa {url}: {e}", file=sys.stderr)
        return []

    listings = []
    for raw in raw_listings:
        href = raw.get("href", "")
        text = raw.get("text", "")
        title = raw.get("title", "")
        if not href:
            continue

        id_m = re.search(r'/(\d+)/d', href)
        if not id_m:
            continue
        uid = f"fotocasa:{id_m.group(1)}"

        price_m = re.search(r'([\d.]+)\s*€', text)
        if not price_m:
            continue
        try:
            price = int(price_m.group(1).replace(".", ""))
        except ValueError:
            continue
        if price > MAX_PRICE or price < 10_000:
            continue

        drop_m = re.search(r'Ha bajado\s*([\d.]+)\s*€', text)
        price_drop = int(drop_m.group(1).replace(".", "")) if drop_m else 0

        days_m = re.search(r'Hace\s+(\d+)\s+d[íi]a', text)
        weeks_m = re.search(r'Hace\s+(\d+)\s+semana', text)
        months_m = re.search(r'Hace\s+(\d+)\s+mes', text)
        if days_m:
            dias = int(days_m.group(1))
        elif weeks_m:
            dias = int(weeks_m.group(1)) * 7
        elif months_m:
            dias = int(months_m.group(1)) * 30
        else:
            dias = None

        habs_m = re.search(r'(\d+)\s*hab', text, re.IGNORECASE)
        banos_m = re.search(r'(\d+)\s*ba[ñn]', text, re.IGNORECASE)
        m2_m = re.search(r'([\d.]+)\s*m[²2]', text)
        floor_m = re.search(r'(\d+[ªa]?\s*[Pp]lanta|[Bb]ajos?|[Áá]tico|[Ss]emigaraje)',
                            text, re.IGNORECASE)

        size_m2 = int(m2_m.group(1).replace(".", "")) if m2_m else 0
        bedrooms = int(habs_m.group(1)) if habs_m else 0
        bathrooms = int(banos_m.group(1)) if banos_m else 0
        floor = floor_m.group(0).strip() if floor_m else ""

        feat_keywords = {
            "terraza": "terraza", "patio": "patio", "jardín": "jardin",
            "jardin": "jardin", "piscina": "piscina", "garaje": "garaje",
            "trastero": "trastero", "ascensor": "ascensor",
            "aire acondicionado": "aire acondicionado",
            "calefacción": "calefaccion", "calefaccion": "calefaccion",
        }
        text_low = text.lower()
        features = list({v for k, v in feat_keywords.items() if k in text_low})

        location = ""
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        for idx, line in enumerate(lines):
            if line == title and idx + 1 < len(lines):
                loc_candidate = lines[idx + 1]
                if "€" not in loc_candidate and len(loc_candidate) > 3:
                    location = loc_candidate
                break
        if not location:
            for line in lines:
                if "," in line and "€" not in line and line != title and len(line) > 5:
                    location = line
                    break

        listings.append({
            "source_url": url,
            "source": "fotocasa.es",
            "scraped_at": datetime.now().isoformat(),
            "uid": uid,
            "pisos_id": uid,
            "url": href,
            "title": title,
            "location": location,
            "price": price,
            "size_m2": size_m2,
            "bedrooms": bedrooms,
            "bathrooms": bathrooms,
            "floor": floor,
            "features": features,
            "detail_features": {},
            "price_drop": price_drop if price_drop else None,
            "_days_on_market": dias,
        })

    return listings


async def scrape_fotocasa_detail(page, prop: dict) -> dict:
    url = prop.get("url", "")
    if not url:
        return prop

    try:
        await page.goto(url, timeout=25000, wait_until="domcontentloaded")
        await asyncio.sleep(1.2)
    except Exception:
        return prop

    try:
        html_snippet = (await page.content())[:2000].lower()
        if any(s in html_snippet for s in ["captcha", "uso indebido", "access denied"]):
            return prop
        detail_text = await page.evaluate(
            "() => document.querySelector('main')?.innerText || document.body?.innerText || ''"
        )
    except Exception:
        return prop

    if not detail_text or len(detail_text) < 50:
        return prop

    detail_lower = detail_text.lower()

    price_m = re.search(r'([\d.]+)\s*€', detail_text)
    if price_m:
        real_price = int(price_m.group(1).replace(".", ""))
        if 10_000 < real_price <= MAX_PRICE:
            prop["price"] = real_price

    m2_m = re.search(r'superficie\s+construida[:\s]*([\d.]+)', detail_lower)
    if not m2_m:
        m2_m = re.search(r'superficie[:\s]*([\d.]+)\s*m', detail_lower)
    if not m2_m:
        m2_m = re.search(r'([\d.]+)\s*m[²2]', detail_text)
    if m2_m and not prop.get("size_m2"):
        prop["size_m2"] = int(m2_m.group(1).replace(".", ""))

    h_m = re.search(r'(\d+)\s*hab', detail_lower)
    if h_m and not prop.get("bedrooms"):
        prop["bedrooms"] = int(h_m.group(1))
    b_m = re.search(r'(\d+)\s*ba[ñn]', detail_lower)
    if b_m and not prop.get("bathrooms"):
        prop["bathrooms"] = int(b_m.group(1))

    fl_m = re.search(r'(\d+[ªa]?\s*planta|bajo|ático)', detail_lower)
    if fl_m and not prop.get("floor"):
        prop["floor"] = fl_m.group(0)

    year_m = re.search(r'(?:año de construcción|construido en)[:\s]*(\d{4})', detail_lower)
    if not year_m:
        year_m = re.search(r'antigüedad[:\s]*(?:más de\s*)?(\d+)\s*año', detail_lower)
        if year_m:
            prop["year_built"] = datetime.now().year - int(year_m.group(1))
    if year_m and "year_built" not in prop:
        prop["year_built"] = int(year_m.group(1))

    energy_m = re.search(r'certificaci[oó]n energ[eé]tica[:\s]*([a-gA-G])\b', detail_text)
    if not energy_m:
        energy_m = re.search(r'energ[eé]tica[:\s]*([a-gA-G])\b', detail_text)
    if energy_m:
        rating = energy_m.group(1).upper()
        if rating in "ABCDEFG":
            prop["energy_rating"] = rating

    feat_keywords = [
        "piscina", "garaje", "trastero", "terraza", "patio",
        "ascensor", "jardín", "jardin", "balcón", "balcon",
        "aire acondicionado", "calefacción", "calefaccion",
        "armario empotrado", "armarios empotrados",
    ]
    seen_feats = set(prop.get("features", []))
    for feat in feat_keywords:
        if feat in detail_lower:
            seen_feats.add(feat)
    prop["features"] = list(seen_feats)
    prop["detail_features"] = {f: True for f in seen_feats}

    desc_m = re.search(
        r'descripci[oó]n\s*\n(.+?)(?:\ncaracter[ií]sticas|\nver m[aá]s|\ncontactar|\ncompartir)',
        detail_text, re.DOTALL | re.IGNORECASE,
    )
    if desc_m:
        prop["description"] = desc_m.group(1).strip()[:2000]

    return prop


class BlockedError(Exception):
    """Lanzada cuando un portal detecta y bloquea el scraper."""
