"""Lanzador del cron de hermes (backend/ops/hermes_launcher.py).

Solo usa la librería estándar: hermes lo ejecuta con su Python 3.14, en el que Playwright no
importa, y él lanza el scorer con el intérprete que sí lo tiene.
"""

import importlib.util
import json
import sys
import threading
from datetime import date, timedelta
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
        "HERMES_DATA_DIR": str(tmp_path / "hermes"),
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
    codigo = cargar().main(
        entorno(tmp_path, scorer, "http://127.0.0.1:9", HOUSESCORE_ESPERA_API="1")
    )
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


def test_con_la_marca_de_hoy_no_ejecuta_el_scorer(tmp_path, api_falsa, capsys):
    centinela = tmp_path / "ejecutado.txt"
    scorer = escribir_scorer(tmp_path, f"open({str(centinela)!r}, 'w').write('x')\n")
    m = cargar()
    marca = tmp_path / "hermes" / "ultima_pasada_ok.txt"
    marca.parent.mkdir()
    marca.write_text(date.today().isoformat(), encoding="utf-8")
    codigo = m.main(entorno(tmp_path, scorer, api_falsa))
    assert codigo == 0
    assert "Ya hay una pasada completa de hoy" in capsys.readouterr().out
    assert not centinela.exists()


def test_con_otra_pasada_en_curso_no_lanza_otra(tmp_path, api_falsa, capsys):
    centinela = tmp_path / "ejecutado.txt"
    scorer = escribir_scorer(tmp_path, f"open({str(centinela)!r}, 'w').write('x')\n")
    m = cargar()
    otro = m._cerrojo(tmp_path / "hermes" / "pasada_en_curso.lock")  # el otro disparo
    try:
        assert m.main(entorno(tmp_path, scorer, api_falsa)) == 0
        assert "Ya hay una pasada en curso" in capsys.readouterr().out
        assert not centinela.exists()
    finally:
        otro.close()
    assert m.main(entorno(tmp_path, scorer, api_falsa)) == 0
    assert centinela.exists()  # liberado el cerrojo, la pasada sí corre


def test_un_scorer_correcto_deja_la_marca_de_hoy(tmp_path, api_falsa):
    scorer = escribir_scorer(tmp_path, "print('ok')\n")
    assert cargar().main(entorno(tmp_path, scorer, api_falsa)) == 0
    marca = tmp_path / "hermes" / "ultima_pasada_ok.txt"
    assert marca.read_text(encoding="utf-8").strip() == date.today().isoformat()


def test_un_scorer_fallido_no_crea_la_marca(tmp_path, api_falsa):
    scorer = escribir_scorer(tmp_path, "import sys\nsys.exit(3)\n")
    assert cargar().main(entorno(tmp_path, scorer, api_falsa)) == 3
    assert not (tmp_path / "hermes" / "ultima_pasada_ok.txt").exists()


def test_una_marca_de_ayer_no_impide_ejecutar(tmp_path, api_falsa):
    centinela = tmp_path / "ejecutado.txt"
    scorer = escribir_scorer(tmp_path, f"open({str(centinela)!r}, 'w').write('x')\n")
    marca = tmp_path / "hermes" / "ultima_pasada_ok.txt"
    marca.parent.mkdir()
    marca.write_text((date.today() - timedelta(days=1)).isoformat(), encoding="utf-8")
    assert cargar().main(entorno(tmp_path, scorer, api_falsa)) == 0
    assert centinela.exists()
    assert marca.read_text(encoding="utf-8").strip() == date.today().isoformat()


def test_el_scorer_no_hereda_las_variables_que_redirigen_a_otro_python(
    tmp_path, api_falsa, capsys, monkeypatch
):
    # hermes ejecuta el lanzador con PYTHONPATH apuntando a su propio entorno (con un Playwright
    # roto para su Python 3.14); si el hijo lo hereda, pisa los paquetes del venv que sí funciona.
    monkeypatch.setenv("PYTHONPATH", "C:/entorno/roto/site-packages")
    monkeypatch.setenv("PYTHONHOME", "C:/otro/python")
    scorer = escribir_scorer(
        tmp_path,
        "import os\n"
        "print('PYTHONPATH=', os.environ.get('PYTHONPATH'))\n"
        "print('PYTHONHOME=', os.environ.get('PYTHONHOME'))\n",
    )
    cargar().main(entorno(tmp_path, scorer, api_falsa))
    salida = capsys.readouterr().out
    assert "PYTHONPATH= None" in salida
    assert "PYTHONHOME= None" in salida


def test_espera_a_que_despierte_la_api(tmp_path, capsys):
    m = cargar()
    t = {"v": 0.0}
    intentos = []

    def comprobar(url):
        intentos.append(url)
        return (len(intentos) >= 3), "503"

    def dormir(s):
        t["v"] += s

    ok, motivo = m.esperar_api(
        "http://x", comprobar=comprobar, dormir=dormir, ahora=lambda: t["v"], presupuesto=180
    )
    assert ok and len(intentos) == 3 and t["v"] > 0


def test_esperar_api_se_rinde_al_agotar_el_presupuesto():
    m = cargar()
    t = {"v": 0.0}

    def dormir(s):
        t["v"] += s

    ok, motivo = m.esperar_api(
        "http://x",
        comprobar=lambda u: (False, "timeout"),
        dormir=dormir,
        ahora=lambda: t["v"],
        presupuesto=60,
    )
    assert not ok and "timeout" in motivo and t["v"] <= 60


def test_mensaje_de_api_caida_nombra_la_url_sin_instrucciones_de_docker(tmp_path, capsys):
    m = cargar()
    scorer = escribir_scorer(tmp_path, "pass\n")
    codigo = m.main(entorno(tmp_path, scorer, "http://127.0.0.1:9", HOUSESCORE_ESPERA_API="1"))
    salida = capsys.readouterr().out
    assert codigo == 2
    assert "http://127.0.0.1:9" in salida
    assert "docker" not in salida.lower()
