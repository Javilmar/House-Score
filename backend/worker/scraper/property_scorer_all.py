#!/usr/bin/env python3
"""
property_scorer_all.py — Orchestrator: ejecuta los 3 lotes en secuencia.
Madrid Sur → Toledo Norte → Idealista. Cada uno con su propio browser.
"""

import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent
SCRIPTS = [
    "property_scorer_madrid.py",
    "property_scorer_toledo.py",
    "property_scorer_idealista.py",
]


def run_script(name: str) -> int:
    script_path = SCRIPTS_DIR / name
    print(f"\n{'#'*60}")
    print(f"# Ejecutando: {name}")
    print(f"{'#'*60}")
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        timeout=600,
    )
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr[:500])
    print(f"\n{'#'*60}")
    print(f"# {name} terminado: exit={result.returncode}")
    print(f"{'#'*60}\n")
    return result.returncode


def main():
    print("▶ property_scorer_all.py — Ejecución completa de propiedades")
    print(f"  📅 {__import__('datetime').datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"  📍 3 lotes: Madrid Sur → Toledo Norte → Idealista")
    print()

    exit_codes = {}
    for script in SCRIPTS:
        try:
            exit_codes[script] = run_script(script)
        except subprocess.TimeoutExpired:
            print(f"❌ {script}: TIMEOUT (5 min)")
            exit_codes[script] = 124
        except Exception as e:
            print(f"❌ {script}: {e}")
            exit_codes[script] = 1

    print("\n" + "=" * 60)
    print("RESUMEN EJECUCIÓN")
    print("=" * 60)
    for script, code in exit_codes.items():
        status = "✅ OK" if code == 0 else f"❌ exit={code}"
        print(f"  {script}: {status}")

    # Código de salida: 0 si todos ok, 1 si alguno falló
    all_ok = all(code == 0 for code in exit_codes.values())
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
