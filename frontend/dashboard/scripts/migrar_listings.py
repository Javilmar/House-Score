"""Migración one-off: fusiona los snapshots diarios (datos/YYYY-MM-DD.json)
en el nuevo almacén canónico (datos/listings.json) más el log de agregados
diarios (datos/historico_diario.json).

Procesa los snapshots en orden cronológico estricto, replicando la misma
lógica de upsert que usa guardar.py, para no perder first_seen/price_drop
históricos. No borra los snapshots originales -- eso lo hace un paso
posterior una vez verificada la migración.

Uso: python dashboard/scripts/migrar_listings.py
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import listings_store

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "datos"
LISTINGS_FILE = DATA_DIR / "listings.json"
HISTORICO_FILE = DATA_DIR / "historico_diario.json"
SNAPSHOT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def snapshots_cronologicos():
    archivos = [f for f in DATA_DIR.glob("*.json") if SNAPSHOT_RE.match(f.stem)]
    return sorted(archivos, key=lambda f: f.stem)


def migrar():
    archivos = snapshots_cronologicos()
    if not archivos:
        print("No se encontraron snapshots diarios para migrar.")
        return 0, 0

    index = {}
    historico = []

    for f in archivos:
        fecha = f.stem
        listings = json.loads(f.read_text(encoding="utf-8"))
        index = listings_store.upsert(index, listings, fecha)
        historico = listings_store.append_daily_aggregate(historico, listings, fecha)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    listings_store.save_listings(LISTINGS_FILE, index)
    listings_store.save_historico(HISTORICO_FILE, historico)

    print(f"{len(index)} listings únicos migrados")
    print(f"{len(historico)} fechas agregadas migradas")
    return len(index), len(historico)


if __name__ == "__main__":
    migrar()
