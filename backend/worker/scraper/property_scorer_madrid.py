#!/usr/bin/env python3
"""
property_scorer_madrid.py — Lote Madrid Sur (pisos.com).

Ejecutar directamente con: python property_scorer_madrid.py
El lote es independiente: abre su propio navegador, scrapea, envia la pasada a la API
(POST /ingest) y cierra. Necesita INGEST_SECRET y la API en marcha (HOUSESCORE_API_URL).
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
    MADRID_SUR, PROPERTY_TYPES, MAX_PRICE, DATA_DIR,
    load_seen_ids, save_seen_ids, load_history,
    assign_market_fields, score_property, build_reference,
    eur_m2_of, reference_eur_m2,
    scrape_search_page, scrape_detail_page, scrape_fotocasa_search, scrape_fotocasa_detail,
    Stealth, BlockedError, REFERENCE_FILE, JSON_OUTPUT,
    ZONA, STATE_FILE,
)
from playwright.async_api import async_playwright


async def main():
    verificar_api()  # falla pronto si la API esta caida, antes de scrapear
    today_str = datetime.now().strftime('%Y-%m-%d')
    today_date = datetime.now().date()
    print(f"▶ property_scorer_madrid.py — Madrid Sur")
    print(f"  📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"  📍 {len(MADRID_SUR)} municipios × {len(PROPERTY_TYPES)} tipos = {len(MADRID_SUR)*len(PROPERTY_TYPES)} búsquedas pisos.com")
    print(f"  📍 {len(MADRID_SUR)} municipios fotocasa")
    print()

    seen_ids = load_seen_ids()
    all_listings = []
    ref_samples = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await Stealth().apply_stealth_async(page)

        count = 0
        total = len(MADRID_SUR) * len(PROPERTY_TYPES)
        for muni in MADRID_SUR:
            for ptype in PROPERTY_TYPES:
                count += 1
                url = f"https://www.pisos.com/venta/{ptype}-{muni}/"
                print(f"[{count}/{total}] 🔍 {muni} ({ptype})... ", end="", flush=True)
                try:
                    listings = await scrape_search_page(page, url)
                    new = 0
                    for l in listings:
                        l["municipio"] = muni
                        l.setdefault("source", "pisos.com")
                        ev = eur_m2_of(l.get("price"), l.get("size_m2"))
                        if ev:
                            ref_samples.append((muni, ev))
                        pid = l.get("pisos_id", "")
                        if pid and pid not in seen_ids:
                            all_listings.append(l)
                            new += 1
                    print(f"{len(listings)} encontrados, {new} nuevos", flush=True)
                except Exception as e:
                    print(f"Error: {e}", flush=True)
                await asyncio.sleep(0.5)

        fc_count = 0
        fc_total = len(MADRID_SUR)
        fc_blocked = False
        fc_ctx = None
        fc_page = None
        _fc_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        print()
        for muni in MADRID_SUR:
            if fc_blocked:
                break
            fc_count += 1
            fc_url = f"https://www.fotocasa.es/es/comprar/viviendas/{muni.replace('_', '-')}/todas-las-zonas/l"
            print(f"[f {fc_count}/{fc_total}] 🔍 {muni} (fotocasa)... ", end="", flush=True)
            if fc_ctx is not None:
                try:
                    await fc_ctx.close()
                except Exception:
                    pass
                fc_ctx = None
                fc_page = None
            try:
                fc_ctx = await browser.new_context(user_agent=_fc_ua)
                await Stealth().apply_stealth_async(fc_ctx)
                fc_page = await fc_ctx.new_page()
                try:
                    fc_listings = await scrape_fotocasa_search(fc_page, fc_url)
                    fc_new = 0
                    for l in fc_listings:
                        l["municipio"] = muni
                        ev = eur_m2_of(l.get("price"), l.get("size_m2"))
                        if ev:
                            ref_samples.append((muni, ev))
                        uid = l.get("pisos_id", "")
                        if uid and uid not in seen_ids:
                            all_listings.append(l)
                            fc_new += 1
                    print(f"{len(fc_listings)} encontrados, {fc_new} nuevos", flush=True)
                except BlockedError:
                    print("⚠️ bloqueado — omitiendo fotocasa esta pasada", flush=True)
                    fc_blocked = True
                    await fc_ctx.close()
                    fc_ctx = None
                    fc_page = None
                except Exception as e:
                    print(f"Error: {e}", flush=True)
            except Exception as e:
                print(f"⚠️ Error iniciando contexto fotocasa ({muni}): {e}", flush=True)
            await asyncio.sleep(0.8)

        # Dedup
        seen_in_batch: set = set()
        unique_listings = []
        for l in sorted(all_listings, key=lambda x: x.get("price", 0)):
            pid = l.get("pisos_id", "")
            if pid and pid not in seen_in_batch:
                seen_in_batch.add(pid)
                unique_listings.append(l)
            elif not pid:
                unique_listings.append(l)
        sim_seen: set = set()
        deduped = []
        for l in unique_listings:
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
        print(f"\n📊 Total new listings (Madrid Sur, deduped): {len(all_listings)}", flush=True)

        # Reference
        reference = build_reference(ref_samples, today_str)
        REFERENCE_FILE.parent.mkdir(parents=True, exist_ok=True)
        REFERENCE_FILE.write_text(json.dumps(reference, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"📐 Reference €/m²: {len(reference['municipios'])} municipios → {REFERENCE_FILE.name}", flush=True)

        if not all_listings:
            print("✅ No hay propiedades nuevas.", flush=True)
            try:
                await browser.close()
            except Exception:
                pass
            return

        history = cargar_historial_api()
        for prop in all_listings:
            assign_market_fields(prop, history, today_str)

        print("\n📊 Pre-scoring...", flush=True)
        for prop in all_listings:
            score_property(prop, reference, today_date)

        all_listings.sort(key=lambda x: (
            not x.get("cumple_requisitos", True),
            x.get("datos_insuficientes", False),
            -x.get("score", 0),
            x.get("price", MAX_PRICE + 1),
        ))

        detail_limit = min(30, len(all_listings))
        print(f"\n🔎 Scraping detail pages for top {detail_limit} properties...", flush=True)
        for i, prop in enumerate(all_listings[:detail_limit]):
            print(f"  [{i+1}/{detail_limit}] {prop.get('title','?')[:50]}... (pre-score: {prop.get('score', 0)})", flush=True)
            try:
                if prop.get("source") == "fotocasa.es" and fc_page is not None:
                    all_listings[i] = await scrape_fotocasa_detail(fc_page, prop)
                else:
                    all_listings[i] = await scrape_detail_page(page, prop)
                score_property(all_listings[i], reference, today_date)
            except Exception as e:
                print(f"    ⚠️ Error: {e}", flush=True)
            await asyncio.sleep(0.3)

        if fc_ctx is not None:
            try:
                await fc_ctx.close()
            except Exception:
                pass

        try:
            await browser.close()
        except Exception:
            pass

        all_listings.sort(key=lambda x: (
            x.get("datos_insuficientes", False),
            -x.get("score", 0),
            x.get("price", MAX_PRICE + 1),
        ))

        for prop in all_listings:
            pid = prop.get("pisos_id", "")
            if pid:
                seen_ids.add(pid)
        save_seen_ids(seen_ids)

        fiables = [p for p in all_listings if not p.get("datos_insuficientes") and p.get("cumple_requisitos", True)]
        top_n = min(10, len(fiables))

        print(f"\n{'='*60}")
        print(f"🏆 TOP {top_n} PROPERTIES — Madrid Sur")
        print(f"{'='*60}")
        if top_n == 0:
            print("No qualifying properties found.")
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
        print(f"📊 Statistics Madrid Sur:")
        print(f"  • Analyzed: {len(all_listings)}")
        if prices:
            print(f"  • Prices: {min(prices):,}€ — {max(prices):,}€")
            print(f"  • Sizes: {min(sizes)}m² — {max(sizes)}m²")
            print(f"  • Avg score: {sum(scores)//max(1,len(scores))}/100")

        # Dashboard JSON
        dashboard_data = []
        for prop in all_listings:
            df = prop.get("detail_features", {})
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
                "detail_features": {k: v for k, v in df.items() if v},
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
        print(f"\n💾 Dashboard JSON saved: {len(dashboard_data)} properties → {JSON_OUTPUT}", flush=True)

        # La API es ahora la fuente de verdad: sustituye a frontend/datos + git push
        try:
            resumen = publicar_pasada(dashboard_data, "madrid")
            print(f"✅ Pasada guardada en la API: {resumen}", flush=True)
        except IngestError as e:
            print(f"❌ {e}", flush=True)
            sys.exit(1)

        print(f"\n✅ property_scorer_madrid.py done", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
