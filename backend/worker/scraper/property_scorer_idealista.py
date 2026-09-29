#!/usr/bin/env python3
"""
property_scorer_idealista.py — Lote Idealista: todos los municipios.
Ejecuta su propio navegador. Independiente del resto.
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
    MAX_PRICE, ALL_MUNICIPALITIES, PROPERTY_TYPES,
    REFERENCE_FILE, DATA_DIR, STATE_FILE, JSON_OUTPUT, IDEALISTA_SESSION,
    load_seen_ids, save_seen_ids, load_history,
    assign_market_fields, score_property, build_reference,
    eur_m2_of, reference_eur_m2, ZONA,
    scrape_idealista_search, scrape_idealista_detail,
    Stealth, BlockedError, _idealista_url,
)
from playwright.async_api import async_playwright


async def main():
    verificar_api()  # falla pronto si la API esta caida, antes de scrapear
    print("▶ property_scorer_idealista.py — Idealista (Madrid Sur + Toledo Norte)")
    print(f"  📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    total = len(ALL_MUNICIPALITIES)
    print(f"  📍 idealista: {total} búsquedas")
    print()

    # Cargar cookies si existen
    cookies = []
    if IDEALISTA_SESSION.exists():
        try:
            cookies = json.loads(IDEALISTA_SESSION.read_text(encoding="utf-8")).get("cookies", [])
            print(f"🍪 Sesión idealista cargada ({len(cookies)} cookies)")
        except Exception:
            pass

    seen_ids = load_seen_ids()
    all_listings = []
    ref_samples = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        i_ctx = None
        i_page = None

        try:
            i_ctx = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
            )
            if cookies:
                await i_ctx.add_cookies(cookies)

            i_page = await i_ctx.new_page()
            await Stealth().apply_stealth_async(i_page)

            count = 0
            for municipality in ALL_MUNICIPALITIES:
                count += 1
                i_url = _idealista_url(municipality)
                print(f"[i {count}/{total}] 🔍 {municipality} (idealista)... ", end="", flush=True)

                try:
                    i_listings = await scrape_idealista_search(i_page, i_url)
                    i_new = 0
                    for l in i_listings:
                        l["municipio"] = municipality
                        ev = eur_m2_of(l.get("price"), l.get("size_m2"))
                        if ev:
                            ref_samples.append((municipality, ev))
                        uid = l.get("pisos_id", "")
                        if uid and uid not in seen_ids:
                            all_listings.append(l)
                            i_new += 1
                    print(f"{len(i_listings)} encontrados, {i_new} nuevos")
                except BlockedError as be:
                    print(f"⚠️ bloqueado ({municipality}) — saltando este municipio")
                except Exception as e:
                    print(f"Error: {e}")

                await asyncio.sleep(1.5)

            if i_ctx:
                await i_ctx.close()
                i_ctx = None
                i_page = None

        except Exception as e:
            print(f"⚠️ Error iniciando contexto idealista: {e}")

        try:
            await browser.close()
        except Exception:
            pass

        # ── Referencia €/m² ──
        today_str = datetime.now().strftime('%Y-%m-%d')
        today_date = datetime.now().date()
        reference = build_reference(ref_samples, today_str)
        REFERENCE_FILE.parent.mkdir(parents=True, exist_ok=True)
        REFERENCE_FILE.write_text(json.dumps(reference, ensure_ascii=False, indent=2),
                                  encoding="utf-8")
        print(f"\n📐 Referencia €/m²: {len(reference['municipios'])} municipios → {REFERENCE_FILE.name}")
        print(f"📊 Total nuevos sin dedup (idealista): {len(all_listings)}")

        if not all_listings:
            print("✅ No hay propiedades nuevas en idealista.")
            return

        history = cargar_historial_api()
        for prop in all_listings:
            assign_market_fields(prop, history, today_str)

        print("\n📊 Pre-puntuando...")
        for prop in all_listings:
            score_property(prop, reference, today_date)

        all_listings.sort(key=lambda x: (not x.get("cumple_requisitos", True),
                                         x.get("datos_insuficientes", False),
                                         -x.get("score", 0), x.get("price", MAX_PRICE + 1)))

        detail_limit = min(15, len(all_listings))
        print(f"\n🔎 Extrayendo detalles de las {detail_limit} mejores propiedades (reabriendo navegador)...")

        # Reabrir contexto para detalles (el anterior ya se cerró)
        async with async_playwright() as p2:
            browser2 = await p2.chromium.launch(headless=True)
            i_ctx2 = await browser2.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
            )
            if cookies:
                await i_ctx2.add_cookies(cookies)
            i_page2 = await i_ctx2.new_page()
            await Stealth().apply_stealth_async(i_page2)

            for i, prop in enumerate(all_listings[:detail_limit]):
                title_short = prop.get("title", "?")[:50]
                print(f"  [{i+1}/{detail_limit}] {title_short}... (score preliminar: {prop.get('score', 0)})")
                try:
                    all_listings[i] = await scrape_idealista_detail(i_page2, prop)
                    score_property(all_listings[i], reference, today_date)
                except Exception as e:
                    print(f"    ⚠️ Error: {e}")
                await asyncio.sleep(0.3)

            await i_ctx2.close()
            try:
                await browser2.close()
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
        print(f"🏆 TOP {top_n} PROPIEDADES — Idealista")
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
        print(f"📊 Estadísticas Idealista:")
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
                "source": prop.get("source", "idealista.com"),
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
            })
        JSON_OUTPUT.write_text(json.dumps(dashboard_data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n💾 Dashboard JSON (idealista): {len(dashboard_data)} listings → {JSON_OUTPUT}")

        # La API es ahora la fuente de verdad: sustituye a frontend/datos + git push
        try:
            resumen = publicar_pasada(dashboard_data, "idealista")
            print(f"✅ Pasada guardada en la API: {resumen}", flush=True)
        except IngestError as e:
            print(f"❌ {e}", flush=True)
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
