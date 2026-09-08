"""Limpieza one-off: aplica retroactivamente la regla corregida de
price_drop/previous_price (spec-005) a datos/listings.json.

Elimina price_drop/previous_price/_candidate_price de cualquier listing
donde previous_price no sea estrictamente mayor que price -- es decir,
donde la "bajada" registrada ya no refleja el estado actual del precio
(bug de spec-005: el campo quedaba congelado para siempre en vez de
recalcularse contra el último precio visto).

Uso: python dashboard/scripts/limpiar_price_drop.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import listings_store

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "datos"
LISTINGS_FILE = DATA_DIR / "listings.json"


def limpiar(index):
    con_drop_antes = sum(1 for i in index.values() if i.get("price_drop"))

    for item in index.values():
        previous_price = item.get("previous_price")
        price = item.get("price")
        if not (
            previous_price is not None and price is not None and previous_price > price
        ):
            item.pop("price_drop", None)
            item.pop("previous_price", None)
        item.pop("_candidate_price", None)

    con_drop_despues = sum(1 for i in index.values() if i.get("price_drop"))
    return con_drop_antes, con_drop_despues


def main():
    index = listings_store.load_listings(LISTINGS_FILE)
    if not index:
        print("No se encontró datos/listings.json o está vacío.")
        return

    antes, despues = limpiar(index)
    listings_store.save_listings(LISTINGS_FILE, index)

    print(f"Listings con price_drop antes: {antes}")
    print(f"Listings con price_drop después: {despues}")


if __name__ == "__main__":
    main()
