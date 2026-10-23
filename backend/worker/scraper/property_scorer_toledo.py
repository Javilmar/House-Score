#!/usr/bin/env python3
"""
property_scorer_toledo.py — Lote Toledo Norte: pisos.com.
Reintenta la navegación tras page crash. Ejecuta su propio navegador. Independiente del resto.
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
    TOLEDO_NORTE, PROPERTY_TYPES,
    score_property, build_reference, eur_m2_of,
    preparar_pasada, candidatos_ficha, ordenar_final, payload_pasada, imprimir_resumen,
    deduplicar_por_id,
    scrape_search_page, scrape_detail_page,
)
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

LIMITE_FICHAS = 15


async def main():
    verificar_api()  # falla pronto si la API esta caida, antes de scrapear
    print("▶ property_scorer_toledo.py — Toledo Norte (pisos.com)")
    print(f"  📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    municipios = TOLEDO_NORTE
    total = len(municipios) * len(PROPERTY_TYPES)
    print(f"  📍 pisos.com: {total} búsquedas (Toledo Norte)")
    print()

    all_listings = []
    ref_samples = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await Stealth().apply_stealth_async(page)

        count = 0

        for municipality in municipios:
            for prop_type in PROPERTY_TYPES:
                count += 1
                url = f"https://www.pisos.com/venta/{prop_type}-{municipality}/"
                print(f"[{count}/{total}] 🔍 {municipality} ({prop_type})... ", end="", flush=True)

                try:
                    listings = await scrape_search_page(page, url, reintentos=2, timeout_ms=30000)
                    for l in listings:
                        l["municipio"] = municipality
                        l.setdefault("source", "pisos.com")
                        ev = eur_m2_of(l.get("price"), l.get("size_m2"))
                        if ev:
                            ref_samples.append((municipality, ev))
                        all_listings.append(l)
                    print(f"{len(listings)} encontrados")
                except Exception as e:
                    print(f"Error: {e}")

                await asyncio.sleep(0.5)

        # ── Referencia €/m² ──
        today_str = datetime.now().strftime('%Y-%m-%d')
        today_date = datetime.now().date()
        reference = build_reference(ref_samples, today_str)
        print(f"\n📐 Referencia €/m²: {len(reference['municipios'])} municipios")
        print(f"📊 Total sin dedup (Toledo Norte): {len(all_listings)}")
        # Un anuncio sale en las búsquedas de varios municipios: una sola copia por anuncio, para
        # que la ficha leída no la pise en la API otra copia sin ficha (gana la última url)
        all_listings = deduplicar_por_id(all_listings)
        print(f"📊 Total sin duplicados (Toledo Norte): {len(all_listings)}")

        if not all_listings:
            print("✅ No hay propiedades en Toledo Norte.")
            try:
                await browser.close()
            except Exception:
                pass
            return

        history = cargar_historial_api()
        reutilizadas = preparar_pasada(all_listings, history, today_str)
        print(f"♻️ Fichas reutilizadas: {reutilizadas}/{len(all_listings)}", flush=True)

        print("\n📊 Pre-puntuando...")
        for prop in all_listings:
            score_property(prop, reference, today_date)

        candidatos = candidatos_ficha(all_listings, LIMITE_FICHAS)
        print(f"\n🔎 Extrayendo detalles de las {len(candidatos)} mejores propiedades sin ficha...")

        for i, prop in enumerate(candidatos):
            title_short = prop.get("title", "?")[:50]
            print(f"  [{i+1}/{len(candidatos)}] {title_short}... (score preliminar: {prop.get('score', 0)})")
            try:
                await scrape_detail_page(page, prop)
                score_property(prop, reference, today_date)
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

        ordenar_final(all_listings)
        imprimir_resumen(all_listings, "Toledo Norte")

        # La API es la fuente de verdad: cada pasada envía todo lo scrapeado
        try:
            resumen = publicar_pasada(payload_pasada(all_listings), "toledo")
            print(f"✅ Pasada guardada en la API: {resumen}", flush=True)
        except IngestError as e:
            print(f"❌ {e}", flush=True)
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
