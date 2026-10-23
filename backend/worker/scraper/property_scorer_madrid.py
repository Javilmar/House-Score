#!/usr/bin/env python3
"""
property_scorer_madrid.py — Lote Madrid Sur (pisos.com).

Ejecutar directamente con: python property_scorer_madrid.py
El lote es independiente: abre su propio navegador, scrapea, envia la pasada a la API
(POST /ingest) y cierra. Necesita INGEST_SECRET y la API en marcha (HOUSESCORE_API_URL).
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
# Raiz de backend/ en el path: el scorer usa el cliente de la API (worker, app)
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from worker.scraper.client import IngestError
from worker.scraper.publicar import cargar_historial_api, publicar_pasada, verificar_api
from property_scorer_common import (
    MADRID_SUR, PROPERTY_TYPES,
    score_property, build_reference, eur_m2_of,
    preparar_pasada, candidatos_ficha, ordenar_final, payload_pasada, imprimir_resumen,
    deduplicar_por_id,
    scrape_search_page, scrape_detail_page, scrape_fotocasa_search, scrape_fotocasa_detail,
    BlockedError,
)
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

LIMITE_FICHAS = 30


async def main():
    verificar_api()  # falla pronto si la API esta caida, antes de scrapear
    today_str = datetime.now().strftime('%Y-%m-%d')
    today_date = datetime.now().date()
    print(f"▶ property_scorer_madrid.py — Madrid Sur")
    print(f"  📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"  📍 {len(MADRID_SUR)} municipios × {len(PROPERTY_TYPES)} tipos = {len(MADRID_SUR)*len(PROPERTY_TYPES)} búsquedas pisos.com")
    print(f"  📍 {len(MADRID_SUR)} municipios fotocasa")
    print()

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
                    for l in listings:
                        l["municipio"] = muni
                        l.setdefault("source", "pisos.com")
                        ev = eur_m2_of(l.get("price"), l.get("size_m2"))
                        if ev:
                            ref_samples.append((muni, ev))
                        all_listings.append(l)
                    print(f"{len(listings)} encontrados", flush=True)
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
                    for l in fc_listings:
                        l["municipio"] = muni
                        ev = eur_m2_of(l.get("price"), l.get("size_m2"))
                        if ev:
                            ref_samples.append((muni, ev))
                        all_listings.append(l)
                    print(f"{len(fc_listings)} encontrados", flush=True)
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
        unique_listings = deduplicar_por_id(all_listings)
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
        print(f"\n📊 Total listings (Madrid Sur, deduped): {len(all_listings)}", flush=True)

        reference = build_reference(ref_samples, today_str)
        print(f"📐 Reference €/m²: {len(reference['municipios'])} municipios", flush=True)

        if not all_listings:
            print("✅ No hay propiedades.", flush=True)
            try:
                await browser.close()
            except Exception:
                pass
            return

        history = cargar_historial_api()
        reutilizadas = preparar_pasada(all_listings, history, today_str)
        print(f"♻️ Fichas reutilizadas: {reutilizadas}/{len(all_listings)}", flush=True)

        print("\n📊 Pre-scoring...", flush=True)
        for prop in all_listings:
            score_property(prop, reference, today_date)

        candidatos = candidatos_ficha(all_listings, LIMITE_FICHAS)
        print(f"\n🔎 Scraping detail pages for top {len(candidatos)} properties without ficha...", flush=True)
        for i, prop in enumerate(candidatos):
            print(f"  [{i+1}/{len(candidatos)}] {prop.get('title','?')[:50]}... (pre-score: {prop.get('score', 0)})", flush=True)
            try:
                if prop.get("source") == "fotocasa.es":
                    if fc_page is None:
                        continue  # fotocasa bloqueado: su ficha queda pendiente
                    await scrape_fotocasa_detail(fc_page, prop)
                else:
                    await scrape_detail_page(page, prop)
                score_property(prop, reference, today_date)
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

        ordenar_final(all_listings)
        imprimir_resumen(all_listings, "Madrid Sur")

        # La API es la fuente de verdad: cada pasada envía todo lo scrapeado
        try:
            resumen = publicar_pasada(payload_pasada(all_listings), "madrid")
            print(f"✅ Pasada guardada en la API: {resumen}", flush=True)
        except IngestError as e:
            print(f"❌ {e}", flush=True)
            sys.exit(1)

        print(f"\n✅ property_scorer_madrid.py done", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
