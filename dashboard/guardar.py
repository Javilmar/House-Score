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
import subprocess
import unicodedata
from datetime import date
from pathlib import Path

import listings_store

DATA_DIR = Path(__file__).resolve().parent.parent / "datos"
REPO_DIR = DATA_DIR.parent
TODAY = date.today().isoformat()

# Municipios de Toledo Norte que ya no son de interés.
# Los pisos scrapeados de estas localidades se descartan antes de guardar.
_TOLEDO_NORTE_BLOQUEADOS = {
    "yuncos",
    "yuncler",
    "yunclillos",
    "cedillo",
    "el viso de san juan",
    "viso de san juan",
    "carranque",
    "recas",
    "lominchar",
    "alameda de la sagra",
    "cabanas de la sagra",
    "villaluenga",
    "anover de tajo",
    "casarrubios",
    "valmojado",
    "magan",
    "cobeja",
    "numancia",
    "pantoja",
    "chozas de canales",
    "bargas",
    "mocejon",
    "burguillos",
    "cobisa",
    "olias",
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
        subprocess.run(
            ["git", "add", "datos/"],
            cwd=REPO_DIR,
            check=True,
            capture_output=True,
            text=True,
        )
        status = subprocess.run(
            ["git", "status", "--porcelain", "datos/"],
            cwd=REPO_DIR,
            capture_output=True,
            text=True,
        )
        if not status.stdout.strip():
            print("   ☁️  Sin cambios que publicar")
            return
        subprocess.run(
            ["git", "commit", "-m", f"datos: pasada {TODAY}"],
            cwd=REPO_DIR,
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "push"], cwd=REPO_DIR, check=True, capture_output=True, text=True
        )
        print("   ☁️  Datos publicados en GitHub")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        detail = getattr(e, "stderr", "") or str(e)
        print(f"   ⚠️  No se pudo publicar a GitHub: {detail.strip()[:200]}")


LISTINGS_FILE = DATA_DIR / "listings.json"
HISTORICO_FILE = DATA_DIR / "historico_diario.json"
DELISTED_THRESHOLD_DAYS = 7


def main():
    if "--stdin" in sys.argv:
        raw = sys.stdin.read()
    elif len(sys.argv) > 1:
        raw = Path(sys.argv[1]).read_text(encoding="utf-8")
    else:
        print(
            "Uso: python guardar.py <archivo.json>  |  cat datos.json | python guardar.py --stdin"
        )
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
        print(
            f"   🚫 Descartados {descartados} pisos de municipios Toledo Norte no permitidos"
        )

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    existing = listings_store.load_listings(LISTINGS_FILE)
    index = listings_store.upsert(existing, new_listings, TODAY)
    index = listings_store.mark_delisted(
        index, TODAY, threshold_days=DELISTED_THRESHOLD_DAYS
    )
    listings_store.save_listings(LISTINGS_FILE, index)

    new_count = len(
        [
            i
            for i in new_listings
            if index.get(i.get("url") or i.get("id") or i.get("title", ""), {}).get(
                "first_seen"
            )
            == TODAY
        ]
    )

    historico = listings_store.load_historico(HISTORICO_FILE)
    activos_hoy = [i for i in index.values() if i.get("status") == "active"]
    historico = listings_store.append_daily_aggregate(historico, activos_hoy, TODAY)
    listings_store.save_historico(HISTORICO_FILE, historico)

    updated_count = len(new_listings) - new_count
    delistados = len([i for i in index.values() if i.get("status") == "delisted"])

    print(f"✅ Guardado en {LISTINGS_FILE}")
    print(f"   🆕 Nuevos: {new_count}")
    print(f"   🔄 Actualizados: {updated_count}")
    print(f"   📊 Activos hoy: {len(activos_hoy)}")
    print(f"   🚪 Retirados (delisted): {delistados}")
    print(f"   🗄️  Total en almacén: {len(index)} listings únicos")

    git_sync()


if __name__ == "__main__":
    main()
