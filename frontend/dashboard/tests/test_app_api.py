"""Tests de la app completa contra una API falsa (spec 002), con streamlit AppTest."""

import os
import sys
import unittest
from pathlib import Path
from unittest import mock

import streamlit as st
from streamlit.testing.v1 import AppTest

sys.path.insert(0, str(Path(__file__).resolve().parent))
# `streamlit run` añade la carpeta del script al path; AppTest no, y app.py hace `import api_datos`
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fake_api import FakeApi, puerto_sin_servidor  # noqa: E402

APP = str(Path(__file__).resolve().parent.parent / "app.py")
# La etiqueta HTML de un KPI (el CSS de la app también contiene ".kpi-card")
KPI_HTML = 'class="kpi-card"'


def ejecutar_app(api_url):
    """Arranca la app con HOUSESCORE_API_URL y devuelve el AppTest ya ejecutado."""
    st.cache_data.clear()  # las cargas de datos se cachean 30 s entre ejecuciones
    with mock.patch.dict(os.environ, {"HOUSESCORE_API_URL": api_url}):
        at = AppTest.from_file(APP, default_timeout=120)
        at.run()
    return at


def texto(at):
    return " ".join(m.value for m in at.markdown)


class AppConApiTests(unittest.TestCase):
    """T007 — la app muestra los datos de la API."""

    def test_la_app_arranca_y_muestra_los_datos_de_la_api(self):
        with FakeApi() as api:
            at = ejecutar_app(api.url)
            peticiones = list(api.peticiones)
        self.assertEqual([e.value for e in at.exception], [])
        self.assertEqual([t.value for t in at.title], ["House Score"])
        visible = texto(at)
        self.assertIn(KPI_HTML, visible)
        self.assertIn("Piso en Getafe", visible)
        self.assertIn("/listings?incluir_retirados=true", peticiones)

    def test_no_se_leen_los_json_del_repositorio(self):
        # Con la API falsa solo hay 4 listings; si se siguiera leyendo frontend/datos aparecerían
        # los ~1.800 del repositorio.
        with FakeApi() as api:
            at = ejecutar_app(api.url)
        self.assertNotIn("Piso en Fuentebella", texto(at))

    def test_un_listing_sin_datos_suficientes_no_rompe_la_pantalla(self):
        with FakeApi() as api:
            at = ejecutar_app(api.url)
        self.assertEqual([e.value for e in at.exception], [])


class AppSinApiTests(unittest.TestCase):
    """T013 — aviso claro si la API falla; ninguna cifra vieja."""

    def assertSinDatos(self, at):
        visible = texto(at)
        self.assertNotIn(KPI_HTML, visible)
        self.assertNotIn("Piso en", visible)

    def test_api_caida_muestra_aviso_con_la_direccion_y_ninguna_cifra(self):
        url = f"http://127.0.0.1:{puerto_sin_servidor()}"
        at = ejecutar_app(url)
        self.assertEqual([e.value for e in at.exception], [])
        self.assertEqual(len(at.error), 1)
        self.assertIn(url, at.error[0].value)
        self.assertIn("No se puede conectar con la API", at.error[0].value)
        self.assertSinDatos(at)

    def test_api_con_error_http_muestra_el_mismo_tipo_de_aviso(self):
        with FakeApi() as api:
            api.estado["/listings"] = 500
            at = ejecutar_app(api.url)
        self.assertEqual([e.value for e in at.exception], [])
        self.assertEqual(len(at.error), 1)
        self.assertIn("HTTP 500", at.error[0].value)
        self.assertSinDatos(at)

    def test_api_sin_listings_es_distinto_de_api_caida(self):
        with FakeApi(listings=[]) as api:
            at = ejecutar_app(api.url)
        self.assertEqual([e.value for e in at.exception], [])
        self.assertEqual(len(at.error), 0)
        avisos = " ".join(w.value for w in at.warning)
        self.assertIn("no tiene listings", avisos)
        self.assertNotIn("guardar.py", avisos)
        self.assertSinDatos(at)

    def test_si_solo_falla_el_historico_el_resto_de_la_app_sigue(self):
        with FakeApi() as api:
            api.estado["/historico"] = 500
            at = ejecutar_app(api.url)
        self.assertEqual([e.value for e in at.exception], [])
        self.assertEqual(len(at.error), 0)
        self.assertIn(KPI_HTML, texto(at))
        self.assertIn("Piso en Getafe", texto(at))
        avisos = " ".join(w.value for w in at.warning)
        self.assertIn("histórico", avisos.lower())

    def test_se_recupera_al_volver_la_api_sin_reiniciar(self):
        st.cache_data.clear()
        with FakeApi() as api, mock.patch.dict(os.environ, {"HOUSESCORE_API_URL": api.url}):
            api.estado["/listings"] = 500
            at = AppTest.from_file(APP, default_timeout=120)
            at.run()
            self.assertEqual(len(at.error), 1)
            api.estado.clear()  # la API vuelve
            at.run()  # misma sesión, misma caché: las excepciones no se cachean
            self.assertEqual(len(at.error), 0)
            self.assertIn("Piso en Getafe", texto(at))


class PieDePaginaTests(unittest.TestCase):
    """T018 — el pie muestra la API, no rutas de ficheros ni el scraper antiguo."""

    def test_el_pie_muestra_la_direccion_de_la_api(self):
        with FakeApi() as api:
            at = ejecutar_app(api.url)
            pie = " ".join(c.value for c in at.caption)
            self.assertIn(api.url, pie)
        self.assertNotIn("property_scorer.py", pie)
        self.assertNotIn("frontend", pie)
        self.assertNotIn("datos", pie.lower().replace("datos de la api", ""))


if __name__ == "__main__":
    unittest.main()
