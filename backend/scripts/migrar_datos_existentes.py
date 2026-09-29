"""Carga frontend/datos y frontend/config en la base de datos (una sola vez).

Uso, desde backend/:
    python -m scripts.migrar_datos_existentes            # usa DATABASE_URL
    python -m scripts.migrar_datos_existentes --datos ../frontend/datos --config ../frontend/config
"""

import argparse
import sys
from pathlib import Path

from app.db.session import get_sessionmaker
from app.services.migracion import BaseDeDatosNoVacia, migrar

RAIZ = Path(__file__).resolve().parents[2]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--datos", type=Path, default=RAIZ / "frontend" / "datos")
    parser.add_argument("--config", type=Path, default=RAIZ / "frontend" / "config")
    args = parser.parse_args()

    with get_sessionmaker()() as session:
        try:
            resumen = migrar(session, args.datos, args.config)
        except BaseDeDatosNoVacia as e:
            print(f"Error: {e}. La migracion solo se ejecuta sobre una base vacia.")
            return 1
    print("Migracion completada:")
    for clave, valor in resumen.items():
        print(f"  {clave}: {valor}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
