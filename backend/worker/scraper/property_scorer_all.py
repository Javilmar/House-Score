#!/usr/bin/env python3
"""
property_scorer_all.py — Orchestrator: ejecuta un lote por zona (ZONAS), en secuencia.
Cada lote es un proceso con su propio browser.
"""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from property_scorer_common import ZONAS

LOTE = Path(__file__).parent / "property_scorer_lote.py"
TIMEOUT_LOTE = 600


def run_lote(zona: str) -> int:
    print(f"\n{'#'*60}")
    print(f"# Ejecutando: {LOTE.name} {zona}")
    print(f"{'#'*60}")
    result = subprocess.run(
        [sys.executable, str(LOTE), zona],
        capture_output=True,
        text=True,
        timeout=TIMEOUT_LOTE,
    )
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr[:500])
    print(f"\n{'#'*60}")
    print(f"# {zona} terminado: exit={result.returncode}")
    print(f"{'#'*60}\n")
    return result.returncode


def main():
    print("▶ property_scorer_all.py — Ejecución completa de propiedades")
    print(f"  📅 {__import__('datetime').datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"  📍 {len(ZONAS)} lotes: {' → '.join(z.etiqueta for z in ZONAS.values())}")
    print()

    exit_codes = {}
    for zona in ZONAS:
        try:
            exit_codes[zona] = run_lote(zona)
        except subprocess.TimeoutExpired:
            print(f"❌ {zona}: TIMEOUT ({TIMEOUT_LOTE // 60} min)")
            exit_codes[zona] = 124
        except Exception as e:
            print(f"❌ {zona}: {e}")
            exit_codes[zona] = 1

    print("\n" + "=" * 60)
    print("RESUMEN EJECUCIÓN")
    print("=" * 60)
    for zona, code in exit_codes.items():
        status = "✅ OK" if code == 0 else f"❌ exit={code}"
        print(f"  {zona}: {status}")

    # Código de salida: 0 si todos ok, 1 si alguno falló
    all_ok = all(code == 0 for code in exit_codes.values())
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
