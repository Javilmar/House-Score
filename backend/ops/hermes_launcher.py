"""Lanzador del job de hermes que ejecuta el scorer del repo y publica en la API.

Por qué existe: hermes ejecuta el `script` de un job con su propio Python 3.14, en el que
Playwright no importa (`greenlet._greenlet`), y solo permite scripts dentro de
`~/AppData/Local/hermes/scripts/`. Este lanzador usa solo la librería estándar, así que funciona
con cualquier intérprete, y lanza `backend/worker/scraper/property_scorer_all.py` con el Python
del entorno de hermes (que sí tiene Playwright, playwright_stealth y httpx).

Instalación: copiar este fichero a `~/AppData/Local/hermes/scripts/housescore_scraper.py` y
apuntar el job con `hermes cron edit <id> --script housescore_scraper.py`.

Variables opcionales (para pruebas): HOUSESCORE_REPO, HOUSESCORE_SCORER, HOUSESCORE_PYTHON,
HOUSESCORE_ENV_FILE, HOUSESCORE_API_URL, HOUSESCORE_TIMEOUT (segundos, 3600 por defecto).

Códigos de salida: el del scorer; 2 = falta algo (API caída o scorer inexistente); 124 = tiempo.
"""

import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

API_URL_DEFECTO = "http://127.0.0.1:8000"  # no "localhost": en Windows añade ~2 s por petición
TIMEOUT_DEFECTO = 3600
# hermes ejecuta el lanzador con estas variables apuntando a su propio entorno (con un Playwright
# roto para su Python 3.14). Si el scorer las hereda, pisan los paquetes de su venv, que sí
# funciona.
_VARS_DE_OTRO_PYTHON = (
    "PYTHONPATH",
    "PYTHONHOME",
    "PYTHONSTARTUP",
    "PYTHONUSERBASE",
    "VIRTUAL_ENV",
)
_CLAVE = re.compile(r"Pasada guardada|❌|⚠️|Traceback|Error|error")


def cargar_env(ruta):
    """Lee un fichero KEY=VALUE (sin comillas ni exports); ignora comentarios y líneas vacías."""
    ruta = Path(ruta)
    if not ruta.exists():
        return {}
    valores = {}
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, _, valor = linea.partition("=")
        valores[clave.strip()] = valor.strip()
    return valores


def _python_del_scorer(env):
    if env.get("HOUSESCORE_PYTHON"):
        return env["HOUSESCORE_PYTHON"]
    venv = (
        Path(__file__).resolve().parent.parent / "hermes-agent" / "venv" / "Scripts" / "python.exe"
    )
    return str(venv) if venv.exists() else sys.executable


def _api_responde(api_url):
    try:
        with urllib.request.urlopen(
            f"{api_url}/listings?municipio=__comprobacion__", timeout=10
        ) as r:
            return r.status == 200, ""
    except Exception as e:  # noqa: BLE001 - cualquier fallo significa "no responde"
        return False, str(e)


def _matar_arbol(proc):
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)
    else:
        proc.kill()


def main(env=None):
    env = dict(os.environ if env is None else env)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    repo = Path(env.get("HOUSESCORE_REPO") or Path.home() / "house-dashboard")
    scorer = Path(
        env.get("HOUSESCORE_SCORER")
        or repo / "backend" / "worker" / "scraper" / "property_scorer_all.py"
    )
    env_file = Path(env.get("HOUSESCORE_ENV_FILE") or repo / "backend" / ".env")
    api_url = (env.get("HOUSESCORE_API_URL") or API_URL_DEFECTO).rstrip("/")
    timeout = int(env.get("HOUSESCORE_TIMEOUT") or TIMEOUT_DEFECTO)

    if not scorer.exists():
        print(f"El scorer no existe: {scorer}")
        return 2
    ok, motivo = _api_responde(api_url)
    if not ok:
        print(
            f"La API no responde en {api_url} ({motivo}). No se ejecuta el scorer para no scrapear "
            "sin poder guardar. Arranca la API: cd backend && docker compose up -d"
        )
        return 2

    sub_env = dict(os.environ)
    for var in _VARS_DE_OTRO_PYTHON:
        sub_env.pop(var, None)
    sub_env.update(cargar_env(env_file))  # INGEST_SECRET vive en backend/.env, no en el cron
    sub_env["HOUSESCORE_API_URL"] = api_url
    sub_env["PYTHONUTF8"] = "1"
    sub_env["PYTHONIOENCODING"] = "utf-8"

    proc = subprocess.Popen(
        [_python_del_scorer(env), "-u", str(scorer)],
        cwd=str(scorer.parent),
        env=sub_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    try:
        salida, _ = proc.communicate(timeout=timeout)
        codigo = proc.returncode
    except subprocess.TimeoutExpired:
        _matar_arbol(proc)
        salida, _ = proc.communicate()
        codigo = 124
        salida += f"\nTiempo máximo agotado ({timeout} s): se detuvo el scorer."

    lineas = salida.splitlines()
    # Idealista bloquea todos los municipios y cada uno imprime su línea: se cuentan aparte
    bloqueados = sum(1 for linea in lineas if "bloqueado (" in linea)
    clave = [linea for linea in lineas if _CLAVE.search(linea) and "bloqueado (" not in linea]
    print("==== RESUMEN ====")
    print(f"Scorer: {scorer}")
    print(f"Terminó con código {codigo}")
    if bloqueados:
        print(f"Idealista: {bloqueados} municipios bloqueados")
    if clave:
        print("Líneas clave:")
        print("\n".join(clave[-40:]))
    print("---- final de la salida ----")
    print("\n".join(lineas[-25:]))
    return codigo


if __name__ == "__main__":
    sys.exit(main())
