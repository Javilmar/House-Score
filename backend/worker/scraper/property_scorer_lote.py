#!/usr/bin/env python3
"""
property_scorer_lote.py — Un lote por zona: pisos.com (+ fotocasa si la zona lo tiene).

Ejecutar con: python property_scorer_lote.py <zona>   (zona: ver ZONAS en property_scorer_common)
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
from worker.scraper.publicar import (
    cargar_descartados, cargar_historial_api, guardar_descartados, publicar_pasada, verificar_api,
)
from property_scorer_common import (
    ZONAS, PROPERTY_TYPES, Zona,
    score_property, build_reference, eur_m2_of, es_problematico,
    preparar_pasada, candidatos_ficha, ordenar_final, payload_pasada, imprimir_resumen,
    deduplicar_por_id,
    scrape_search_page, scrape_detail_page, scrape_fotocasa_search, scrape_fotocasa_detail,
    BlockedError,
)
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

_FC_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
          "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")


def _sin_problematicos(listings: list[dict], descartados: dict[str, str], hoy: str) -> list[dict]:
    """Quita lo ya descartado y lo que es problemático ahora (y lo apunta en `descartados`)."""
    quedan = []
    for l in listings:
        url = l.get("url", "")
        if url and url in descartados:
            continue
        if es_problematico(l):
            if url:
                descartados[url] = hoy
            continue
        quedan.append(l)
    return quedan


def _sin_similares(listings: list[dict]) -> list[dict]:
    """Mismo municipio, precio (al millar), m² y habitaciones: el mismo piso en otro anuncio."""
    vistos: set = set()
    unicos = []
    for l in listings:
        clave = (
            l.get("municipio", ""),
            round((l.get("price", 0) or 0) / 1000),
            l.get("size_m2", 0) or 0,
            l.get("bedrooms", 0) or 0,
        )
        if clave not in vistos:
            vistos.add(clave)
            unicos.append(l)
    return unicos


async def main(zona: Zona):
    verificar_api()  # falla pronto si la API esta caida, antes de scrapear
    today_str = datetime.now().strftime('%Y-%m-%d')
    today_date = datetime.now().date()
    municipios = zona.municipios
    print(f"▶ property_scorer_lote.py — {zona.etiqueta} (tope {zona.tope:,} €)")
    print(f"  📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"  📍 {len(municipios)} municipios × {len(PROPERTY_TYPES)} tipos = "
          f"{len(municipios)*len(PROPERTY_TYPES)} búsquedas pisos.com")
    if zona.fotocasa:
        print(f"  📍 {len(municipios)} municipios fotocasa")
    print()

    all_listings = []
    ref_samples = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await Stealth().apply_stealth_async(page)

        count = 0
        total = len(municipios) * len(PROPERTY_TYPES)
        for muni in municipios:
            for ptype in PROPERTY_TYPES:
                count += 1
                url = f"https://www.pisos.com/venta/{ptype}-{muni}/"
                print(f"[{count}/{total}] 🔍 {muni} ({ptype})... ", end="", flush=True)
                try:
                    # 2 intentos y 30 s: algunas páginas cuelgan la pestaña (page crash)
                    listings = await scrape_search_page(page, url, zona.tope,
                                                        reintentos=2, timeout_ms=30000)
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

        fc_ctx = None
        fc_page = None
        if zona.fotocasa:
            print()
            for fc_count, muni in enumerate(municipios, 1):
                fc_url = f"https://www.fotocasa.es/es/comprar/viviendas/{muni.replace('_', '-')}/todas-las-zonas/l"
                print(f"[f {fc_count}/{len(municipios)}] 🔍 {muni} (fotocasa)... ", end="", flush=True)
                if fc_ctx is not None:
                    try:
                        await fc_ctx.close()
                    except Exception:
                        pass
                    fc_ctx = None
                    fc_page = None
                try:
                    fc_ctx = await browser.new_context(user_agent=_FC_UA)
                    await Stealth().apply_stealth_async(fc_ctx)
                    fc_page = await fc_ctx.new_page()
                    try:
                        fc_listings = await scrape_fotocasa_search(fc_page, fc_url, zona.tope)
                        for l in fc_listings:
                            l["municipio"] = muni
                            ev = eur_m2_of(l.get("price"), l.get("size_m2"))
                            if ev:
                                ref_samples.append((muni, ev))
                            all_listings.append(l)
                        print(f"{len(fc_listings)} encontrados", flush=True)
                    except BlockedError:
                        print("⚠️ bloqueado — omitiendo fotocasa esta pasada", flush=True)
                        await fc_ctx.close()
                        fc_ctx = None
                        fc_page = None
                        break
                    except Exception as e:
                        print(f"Error: {e}", flush=True)
                except Exception as e:
                    print(f"⚠️ Error iniciando contexto fotocasa ({muni}): {e}", flush=True)
                await asyncio.sleep(0.8)

        # Un anuncio sale en las búsquedas de varios municipios: una sola copia por anuncio, para
        # que la ficha leída no la pise en la API otra copia sin ficha (gana la última url)
        all_listings = _sin_similares(deduplicar_por_id(all_listings))
        descartados = cargar_descartados()
        antes = len(all_listings)
        all_listings = _sin_problematicos(all_listings, descartados, today_str)
        print(f"\n📊 Total listings ({zona.etiqueta}, deduped): {len(all_listings)} "
              f"({antes - len(all_listings)} descartados: sin posesión, okupados, subastas…)",
              flush=True)

        reference = build_reference(ref_samples, today_str)
        print(f"📐 Reference €/m²: {len(reference['municipios'])} municipios", flush=True)

        if not all_listings:
            print("✅ No hay propiedades.", flush=True)
            guardar_descartados(descartados)
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

        candidatos = candidatos_ficha(all_listings, zona.limite_fichas)
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

        # La ficha puede revelar lo que el listado no decía (p. ej. «sin posesión»)
        all_listings = _sin_problematicos(all_listings, descartados, today_str)
        guardar_descartados(descartados)

        ordenar_final(all_listings)
        imprimir_resumen(all_listings, zona.etiqueta)

        # La API es la fuente de verdad: cada pasada envía todo lo scrapeado
        try:
            resumen = publicar_pasada(payload_pasada(all_listings), zona.clave)
            print(f"✅ Pasada guardada en la API: {resumen}", flush=True)
        except IngestError as e:
            print(f"❌ {e}", flush=True)
            sys.exit(1)

        print(f"\n✅ property_scorer_lote.py {zona.clave} done", flush=True)


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ZONAS:
        print(f"Uso: python property_scorer_lote.py <{'|'.join(ZONAS)}>", file=sys.stderr)
        sys.exit(2)
    asyncio.run(main(ZONAS[sys.argv[1]]))
