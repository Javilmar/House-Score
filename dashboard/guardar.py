"""
Helper para guardar resultados de una pasada de búsqueda de vivienda.
Uso: python guardar.py <archivo_entrada.json>
     o pipe: cat resultados.json | python guardar.py --stdin

El archivo de entrada debe ser un array JSON de listings:
[
  {
    "title": "Piso en Chamberí",
    "price": 250000,
    "score": 8.5,
    "location": "Chamberí, Madrid",
    "m2": 80,
    "rooms": 3,
    "bathrooms": 2,
    "url": "https://...",
    "source": "idealista",
    ...
  },
  ...
]
"""

import json
import sys
import os
import subprocess
import unicodedata
from datetime import date, datetime
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "datos"
REPO_DIR = DATA_DIR.parent
TODAY = date.today().isoformat()

# Municipios de Toledo Norte que ya no son de interés.
# Los pisos scrapeados de estas localidades se descartan antes de guardar.
_TOLEDO_NORTE_BLOQUEADOS = {
    "yuncos", "yuncler", "yunclillos", "cedillo",
    "el viso de san juan", "viso de san juan", "carranque",
    "recas", "lominchar", "alameda de la sagra", "cabanas de la sagra",
    "villaluenga", "anover de tajo", "casarrubios", "valmojado",
    "magan", "cobeja", "numancia", "pantoja", "chozas de canales",
    "bargas", "mocejon", "burguillos", "cobisa", "olias",
}


def _sin_acentos(s):
    s = unicodedata.normalize("NFKD", str(s))
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def _bloqueado(item):
    """Devuelve True si el listing pertenece a un municipio de Toledo Norte descartado."""
    muni = _sin_acentos(item.get("municipio") or "")
    return muni in _TOLEDO_NORTE_BLOQUEADOS


def git_sync():
    """Empuja los datos del día a GitHub para que el dashboard en la nube los vea.
    Best-effort: si git no está configurado o falla, no rompe la pasada."""
    try:
        subprocess.run(["git", "add", "datos/"], cwd=REPO_DIR, check=True,
                       capture_output=True, text=True)
        status = subprocess.run(["git", "status", "--porcelain", "datos/"],
                                cwd=REPO_DIR, capture_output=True, text=True)
        if not status.stdout.strip():
            print("   ☁️  Sin cambios que publicar")
            return
        subprocess.run(["git", "commit", "-m", f"datos: pasada {TODAY}"],
                       cwd=REPO_DIR, check=True, capture_output=True, text=True)
        subprocess.run(["git", "push"], cwd=REPO_DIR, check=True,
                       capture_output=True, text=True)
        print("   ☁️  Datos publicados en GitHub")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        detail = getattr(e, "stderr", "") or str(e)
        print(f"   ⚠️  No se pudo publicar a GitHub: {detail.strip()[:200]}")


def load_existing():
    """Carga todos los listings históricos (diccionario indexado por url)."""
    index = {}
    if DATA_DIR.exists():
        for f in sorted(DATA_DIR.glob("*.json")):
            if f.stem == TODAY:
                continue  # el de hoy se procesa aparte
            try:
                listings = json.loads(f.read_text(encoding="utf-8"))
                for item in listings:
                    key = item.get("url") or item.get("id") or item.get("title", "")
                    if key:
                        index[key] = item
            except (json.JSONDecodeError, IOError):
                continue
    return index


def merge(new_listings, existing_index):
    """Merge nuevos listings con el índice histórico. Retorna lista actualizada."""
    updated_index = dict(existing_index)  # copia
    merged = []
    today_str = TODAY

    for item in new_listings:
        key = item.get("url") or item.get("id") or item.get("title", "")
        if not key:
            merged.append(item)
            continue

        # Asegurar que tenga fecha
        if "first_seen" not in item:
            item["first_seen"] = today_str
        item["last_seen"] = today_str

        if key in updated_index:
            old = updated_index[key]
            # Mantener first_seen original
            item["first_seen"] = old.get("first_seen", item["first_seen"])
            # Detectar bajada de precio
            old_price = old.get("price")
            new_price = item.get("price")
            if old_price and new_price and new_price < old_price:
                item["price_drop"] = old_price - new_price
                item["previous_price"] = old_price
            elif old.get("previous_price"):
                item["previous_price"] = old.get("previous_price")
            if old.get("price_drop"):
                item["price_drop"] = old.get("price_drop")

        updated_index[key] = item
        merged.append(item)

    return merged


def main():
    if "--stdin" in sys.argv:
        raw = sys.stdin.read()
    elif len(sys.argv) > 1:
        raw = Path(sys.argv[1]).read_text(encoding="utf-8")
    else:
        print("Uso: python guardar.py <archivo.json>  |  cat datos.json | python guardar.py --stdin")
        sys.exit(1)

    new_listings = json.loads(raw)
    if not isinstance(new_listings, list):
        print("Error: el JSON debe ser un array de listings")
        sys.exit(1)

    # Descartar pisos de municipios Toledo Norte no permitidos
    antes = len(new_listings)
    new_listings = [item for item in new_listings if not _bloqueado(item)]
    descartados = antes - len(new_listings)
    if descartados:
        print(f"   🚫 Descartados {descartados} pisos de municipios Toledo Norte no permitidos")

    existing = load_existing()
    merged = merge(new_listings, existing)

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Cargar lo que ya hubiera hoy y hacer merge
    today_file = DATA_DIR / f"{TODAY}.json"
    today_existing = []
    today_index = {}
    if today_file.exists():
        try:
            today_existing = json.loads(today_file.read_text(encoding="utf-8"))
            for item in today_existing:
                key = item.get("url") or item.get("id") or item.get("title", "")
                if key:
                    today_index[key] = item
        except (json.JSONDecodeError, IOError):
            pass

    # Merge con lo de hoy
    for item in merged:
        key = item.get("url") or item.get("id") or item.get("title", "")
        if key and key not in today_index:
            today_index[key] = item

    final = sorted(today_index.values(), key=lambda x: x.get("score", 0), reverse=True)
    today_file.write_text(json.dumps(final, ensure_ascii=False, indent=2), encoding="utf-8")

    new_count = len([i for i in merged if i.get("first_seen") == TODAY])
    updated_count = len(merged) - new_count

    print(f"✅ Guardado en {today_file}")
    print(f"   🆕 Nuevos: {new_count}")
    print(f"   🔄 Actualizados: {updated_count}")
    print(f"   📊 Total hoy: {len(final)}")

    # También generar el histórico completo (para el dashboard)
    full_index = existing
    for item in merged:
        key = item.get("url") or item.get("id") or item.get("title", "")
        if key:
            full_index[key] = item
    print(f"   🗄️  Total histórico: {len(full_index)} listings únicos")

    git_sync()


if __name__ == "__main__":
    main()
