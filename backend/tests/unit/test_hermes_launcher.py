"""Lanzador del cron de hermes (backend/ops/hermes_launcher.py).

Solo usa la librería estándar: hermes lo ejecuta con su Python 3.14, en el que Playwright no
importa, y él lanza el scorer con el intérprete que sí lo tiene.
"""

import importlib.util
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

RUTA = Path(__file__).resolve().parents[2] / "ops" / "hermes_launcher.py"


def cargar():
    spec = importlib.util.spec_from_file_location("hermes_launcher", RUTA)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


@pytest.fixture
def api_falsa():
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            cuerpo = json.dumps([]).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(cuerpo)))
            self.end_headers()
            self.wfile.write(cuerpo)

    servidor = HTTPServer(("127.0.0.1", 0), H)
    hilo = threading.Thread(target=servidor.serve_forever, daemon=True)
    hilo.start()
    yield f"http://127.0.0.1:{servidor.server_address[1]}"
    servidor.shutdown()
    servidor.server_close()


def escribir_scorer(tmp_path, cuerpo):
    ruta = tmp_path / "scorer.py"
    ruta.write_text(cuerpo, encoding="utf-8")
    return ruta


def entorno(tmp_path, scorer, api, **extra):
    env = {
        "HOUSESCORE_SCORER": str(scorer),
        "HOUSESCORE_PYTHON": sys.executable,
        "HOUSESCORE_API_URL": api,
        "HOUSESCORE_ENV_FILE": str(tmp_path / "no-existe.env"),
    }
    env.update(extra)
    return env


def test_cargar_env_ignora_comentarios_y_lineas_vacias(tmp_path):
    m = cargar()
    f = tmp_path / ".env"
    f.write_text(
        "# comentario\n\nINGEST_SECRET=abc=123\n  OTRA = valor \nSINIGUAL\n", encoding="utf-8"
    )
    assert m.cargar_env(f) == {"INGEST_SECRET": "abc=123", "OTRA": "valor"}


def test_cargar_env_inexistente_devuelve_vacio(tmp_path):
    assert cargar().cargar_env(tmp_path / "nada.env") == {}


def test_ejecuta_el_scorer_pasa_el_secreto_y_devuelve_su_codigo(tmp_path, api_falsa, capsys):
    scorer = escribir_scorer(
        tmp_path,
        "import os\n"
        "print('secreto:', os.environ.get('INGEST_SECRET'))\n"
        "print('Pasada guardada en la API: {}')\n",
    )
    env_file = tmp_path / ".env"
    env_file.write_text("INGEST_SECRET=s3cret\n", encoding="utf-8")
    m = cargar()
    codigo = m.main(entorno(tmp_path, scorer, api_falsa, HOUSESCORE_ENV_FILE=str(env_file)))
    salida = capsys.readouterr().out
    assert codigo == 0
    assert "secreto: s3cret" in salida  # el scorer recibe el secreto sin que esté en el cron
    assert "Pasada guardada" in salida


def test_propaga_el_codigo_de_error_del_scorer_y_lo_resume(tmp_path, api_falsa, capsys):
    scorer = escribir_scorer(tmp_path, "import sys\nprint('❌ el lote falló')\nsys.exit(3)\n")
    codigo = cargar().main(entorno(tmp_path, scorer, api_falsa))
    salida = capsys.readouterr().out
    assert codigo == 3
    assert "RESUMEN" in salida and "código 3" in salida
    assert "❌ el lote falló" in salida


def test_con_la_api_caida_no_ejecuta_el_scorer(tmp_path, capsys):
    marca = tmp_path / "ejecutado.txt"
    scorer = escribir_scorer(tmp_path, f"open({str(marca)!r}, 'w').write('x')\n")
    codigo = cargar().main(entorno(tmp_path, scorer, "http://127.0.0.1:9"))
    salida = capsys.readouterr().out
    assert codigo == 2
    assert "API" in salida and "no responde" in salida
    assert not marca.exists()


def test_tiempo_maximo_agotado_devuelve_error(tmp_path, api_falsa, capsys):
    scorer = escribir_scorer(tmp_path, "import time\ntime.sleep(30)\n")
    codigo = cargar().main(entorno(tmp_path, scorer, api_falsa, HOUSESCORE_TIMEOUT="1"))
    assert codigo == 124
    assert "tiempo" in capsys.readouterr().out.lower()


def test_falta_el_scorer(tmp_path, api_falsa, capsys):
    codigo = cargar().main(entorno(tmp_path, tmp_path / "no-existe.py", api_falsa))
    assert codigo == 2
    assert "no existe" in capsys.readouterr().out
