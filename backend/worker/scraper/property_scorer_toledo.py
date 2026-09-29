#!/usr/bin/env python3
"""
property_scorer_toledo.py — Lote Toledo Norte: pisos.com.
Maneja page crashes. Ejecuta su propio navegador. Independiente del resto.
"""

import asyncio
import json
import sys
from datetime import datetime, date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
# Raiz de backend/ en el path: el scorer usa el cliente de la API (worker, app)
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from worker.scraper.client import IngestError
from worker.scraper.publicar import cargar_historial_api, publicar_pasada, verificar_api
from property_scorer_common import (
    MAX_PRICE, TOLEDO_NORTE, PROPERTY_TYPES,
    REFERENCE_FILE, DATA_DIR, STATE_FILE, JSON_OUTPUT,
    load_seen_ids, save_seen_ids, load_history,
    assign_market_fields, score_property, build_reference,
    eur_m2_of, reference_eur_m2, ZONA,
    scrape_search_page, scrape_detail_page,
    Stealth,
)
from playwright.async_api import async_playwright


async def scrape_search_page_resilient(page, url: str, max_retries: int = 2, timeout: int = 30000) -> list:
    """Versión resistente de scrape_search_page: reintenta tras page crash."""
    last_error = None
    for attempt in range(max_retries):
        try:
            await page.goto(url, timeout=timeout, wait_until="domcontentloaded")
            await asyncio.sleep(2)
            # Si llegamos aquí sin excepción, extraemos
            break
        except asyncio.TimeoutError:
            last_error = "Timeout al cargar página"
            print(f"    ⚠️ Timeout (intentos restantes: {max_retries - attempt - 1})", file=sys.stderr)
            await asyncio.sleep(1)
        except Exception as e:
            last_error = e
            print(f"    ⚠️ Intento {attempt+1}: {type(e).__name__} — reintentando...", file=sys.stderr)
            await asyncio.sleep(1)
    else:
        print(f"  ⚠️ Error cargando {url}: {last_error}", file=sys.stderr)
        return []

    # Extraer listings (código copiado de property_scorer_common para no depender de la función original)
    import re
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
        prop = {"source_url": url, "scraped_at": datetime.now().isoformat()}
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
            if found_price and not found_title and line in ("TOP", "NUEVO", "Oportunidad", "Exclusivo", "Céntrico", "Centrico", "Calidades superiores", "Con precio rebajado"):
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
            prop["pisos_id"] = m.group(1) if m else link_data[i]["href"]
        else:
            prop["url"] = ""
            prop["pisos_id"] = ""

        listings.append(prop)

    return listings


async def main():
    verificar_api()  # falla pronto si la API esta caida, antes de scrapear
    print("▶ property_scorer_toledo.py — Toledo Norte (pisos.com)")
    print(f"  📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    municipios = TOLEDO_NORTE
    total = len(municipios) * len(PROPERTY_TYPES)
    print(f"  📍 pisos.com: {total} búsquedas (Toledo Norte)")
    print()

    seen_ids = load_seen_ids()
    all_listings = []
    ref_samples = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await Stealth().apply_stealth_async(page)

        count = 0
        crashed_municipios = []

        for municipality in municipios:
            for prop_type in PROPERTY_TYPES:
                count += 1
                url = f"https://www.pisos.com/venta/{prop_type}-{municipality}/"
                print(f"[{count}/{total}] 🔍 {municipality} ({prop_type})... ", end="", flush=True)

                try:
                    listings = await scrape_search_page_resilient(page, url)
                    new = 0
                    for l in listings:
                        l["municipio"] = municipality
                        l.setdefault("source", "pisos.com")
                        ev = eur_m2_of(l.get("price"), l.get("size_m2"))
                        if ev:
                            ref_samples.append((municipality, ev))
                        pid = l.get("pisos_id", "")
                        if pid and pid not in seen_ids:
                            all_listings.append(l)
                            new += 1
                    print(f"{len(listings)} encontrados, {new} nuevos")
                except Exception as e:
                    print(f"Error: {e}")
                    crashed_municipios.append(municipality)

                await asyncio.sleep(0.5)

        # ── Referencia €/m² ──
        today_str = datetime.now().strftime('%Y-%m-%d')
        today_date = datetime.now().date()
        reference = build_reference(ref_samples, today_str)
        REFERENCE_FILE.parent.mkdir(parents=True, exist_ok=True)
        REFERENCE_FILE.write_text(json.dumps(reference, ensure_ascii=False, indent=2),
                                  encoding="utf-8")
        print(f"\n📐 Referencia €/m²: {len(reference['municipios'])} municipios → {REFERENCE_FILE.name}")
        print(f"📊 Total nuevos sin dedup (Toledo Norte): {len(all_listings)}")

        if not all_listings:
            print("✅ No hay propiedades nuevas en Toledo Norte.")
            try:
                await browser.close()
            except Exception:
                pass
            return

        history = cargar_historial_api()
        for prop in all_listings:
            assign_market_fields(prop, history, today_str)

        print("\n📊 Pre-puntuando...")
        for prop in all_listings:
            score_property(prop, reference, today_date)

        all_listings.sort(key=lambda x: (x.get("datos_insuficientes", False),
                                         -x.get("score", 0), x.get("price", MAX_PRICE + 1)))

        detail_limit = min(15, len(all_listings))
        print(f"\n🔎 Extrayendo detalles de las {detail_limit} mejores propiedades...")

        for i, prop in enumerate(all_listings[:detail_limit]):
            title_short = prop.get("title", "?")[:50]
            print(f"  [{i+1}/{detail_limit}] {title_short}... (score preliminar: {prop.get('score', 0)})")
            try:
                all_listings[i] = await scrape_detail_page(page, prop)
                score_property(all_listings[i], reference, today_date)
            except Exception as e:
                print(f"    ⚠️ Error: {e}")
            await asyncio.sleep(0.3)

        try:
            await browser.close()
        except Exception:
            pass

        # ── Dedup ──
        sim_seen: set = set()
        deduped = []
        for l in all_listings:
            sim_key = (
                l.get("municipio", ""),
                round((l.get("price", 0) or 0) / 1000),
                l.get("size_m2", 0) or 0,
                l.get("bedrooms", 0) or 0,
            )
            if sim_key not in sim_seen:
                sim_seen.add(sim_key)
                deduped.append(l)
        all_listings = deduped
        print(f"\n📊 Total después de dedup (Toledo Norte): {len(all_listings)}")

        all_listings.sort(key=lambda x: (x.get("datos_insuficientes", False),
                                         -x.get("score", 0), x.get("price", MAX_PRICE + 1)))

        for prop in all_listings:
            pid = prop.get("pisos_id", "")
            if pid:
                seen_ids.add(pid)
        save_seen_ids(seen_ids)

        # ── TOP ──
        fiables = [p for p in all_listings if not p.get("datos_insuficientes") and p.get("cumple_requisitos", True)]
        top_n = min(10, len(fiables))

        print(f"\n{'='*60}")
        print(f"🏆 TOP {top_n} PROPIEDADES — Toledo Norte")
        print(f"{'='*60}")

        if top_n == 0:
            print("No se encontraron propiedades valorables.")
        else:
            for i, prop in enumerate(fiables[:top_n]):
                s = prop.get("score", 0)
                bar = "⭐" * min(10, s // 10) + "☆" * (10 - min(10, s // 10))
                print(f"\n{'─'*50}")
                print(f"#{i+1}  {bar}  {s}/100")
                print(f"  🏷️ {prop.get('title', 'Sin título')}")
                print(f"  📍 {prop.get('location', 'Sin ubicación')}")
                print(f"  💰 {prop.get('price', 0):,}€")
                print(f"  📐 {prop.get('size_m2', 0)} m² | {prop.get('bedrooms', 0)} habs | {prop.get('bathrooms', 0)} baños")
                if prop.get("floor"):
                    print(f"  🏢 {prop['floor']}")
                if prop.get("year_built"):
                    print(f"  📅 {prop['year_built']} | {prop.get('conservation', '')}")
                if prop.get("url"):
                    print(f"  🔗 {prop['url']}")
                for detail in prop.get("score_details", []):
                    print(f"    {detail}")

        prices = [p.get("price", 0) for p in all_listings]
        sizes = [p.get("size_m2", 0) for p in all_listings]
        scores = [p.get("score", 0) for p in all_listings]

        print(f"\n{'='*60}")
        print(f"📊 Estadísticas Toledo Norte:")
        print(f"  • Analizadas: {len(all_listings)}")
        print(f"  • Precios: {min(prices):,}€ — {max(prices):,}€" if prices else "  • Precios: N/A")
        print(f"  • Score medio: {sum(scores)//max(1,len(scores))}/100" if scores else "  • Score: N/A")

        # ── JSON dashboard ──
        dashboard_data = []
        for prop in all_listings:
            detail_feats = prop.get("detail_features", {})
            dashboard_data.append({
                "title": prop.get("title", "Sin título"),
                "price": prop.get("price", 0),
                "score": prop.get("score", 0),
                "location": prop.get("location", ""),
                "m2": prop.get("size_m2", 0),
                "rooms": prop.get("bedrooms", 0),
                "bathrooms": prop.get("bathrooms", 0),
                "url": prop.get("url", ""),
                "source": prop.get("source", "pisos.com"),
                "floor": prop.get("floor", ""),
                "year_built": prop.get("year_built", 0),
                "conservation": prop.get("conservation", ""),
                "energy_rating": prop.get("energy_rating", ""),
                "description": prop.get("description", "")[:500],
                "features": prop.get("features", []),
                "detail_features": {k: v for k, v in detail_feats.items() if v},
                "pisos_id": prop.get("pisos_id", ""),
                "score_details": prop.get("score_details", []),
                "eur_m2": prop.get("eur_m2", 0),
                "municipio": prop.get("municipio", ""),
                "first_seen": prop.get("first_seen", ""),
                "last_seen": prop.get("last_seen", ""),
                "previous_price": prop.get("previous_price"),
                "price_drop": prop.get("price_drop"),
                "datos_insuficientes": prop.get("datos_insuficientes", False),
                "exterior": prop.get("exterior", False),
                "cumple_requisitos": prop.get("cumple_requisitos", True),
                "crashed_municipio": municipality in crashed_municipios,
            })
        JSON_OUTPUT.write_text(json.dumps(dashboard_data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n💾 Dashboard JSON (Toledo Norte): {len(dashboard_data)} listings → {JSON_OUTPUT}")

        # La API es ahora la fuente de verdad: sustituye a frontend/datos + git push
        try:
            resumen = publicar_pasada(dashboard_data, "toledo")
            print(f"✅ Pasada guardada en la API: {resumen}", flush=True)
        except IngestError as e:
            print(f"❌ {e}", flush=True)
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
