"""Tests del adaptador de la API (spec 002)."""

import math
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import api_datos  # noqa: E402
from fake_api import (  # noqa: E402
    FakeApi,
    historico_de_ejemplo,
    listing_api,
    listings_de_ejemplo,
    puerto_sin_servidor,
)


def fila(df, url):
    return df[df["url"] == url].iloc[0]


class ListingsADataframeTests(unittest.TestCase):
    """T004 — traducción de /listings a las columnas del dashboard."""

    def setUp(self):
        self.df = api_datos.listings_a_dataframe(listings_de_ejemplo())
        self.getafe = fila(self.df, "https://www.pisos.com/comprar/piso-getafe-1/")

    def test_mapea_los_campos_principales(self):
        g = self.getafe
        self.assertEqual(g["title"], "Piso en Getafe")
        self.assertEqual(g["price"], 180000)
        self.assertEqual(g["m2"], 80)
        self.assertEqual(g["rooms"], 3)
        self.assertEqual(g["bathrooms"], 2)
        self.assertEqual(g["source"], "pisos.com")
        self.assertEqual(g["municipio"], "getafe")
        self.assertEqual(g["score"], 71.0)
        self.assertEqual(g["price_drop"], 5000)
        self.assertEqual(g["previous_price"], 185000)

    def test_fechas_como_timestamp(self):
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(self.df["first_seen"]))
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(self.df["last_seen"]))
        self.assertEqual(self.getafe["first_seen"], pd.Timestamp("2026-09-01"))
        self.assertEqual(self.getafe["last_seen"], pd.Timestamp("2026-09-29"))

    def test_estado_se_traduce_a_status_del_dashboard(self):
        self.assertEqual(self.getafe["status"], "active")
        parla = fila(self.df, "https://www.pisos.com/comprar/piso-parla-2/")
        self.assertEqual(parla["status"], "delisted")

    def test_el_detalle_se_vuelca_como_columnas(self):
        g = self.getafe
        self.assertEqual(g["location"], "Centro (Getafe)")
        self.assertEqual(g["description"], "Piso luminoso con terraza")
        self.assertEqual(list(g["score_details"]), ["Valor vs zona (+20)", "Amplio: 80m2 (+10)"])
        self.assertEqual(list(g["features"]), ["Ascensor", "Terraza"])
        self.assertEqual(g["energy_rating"], "D")

    def test_una_clave_del_detalle_no_pisa_una_columna_principal(self):
        item = listing_api(detalle={"title": "OTRO", "price": 1, "location": "x"})
        df = api_datos.listings_a_dataframe([item])
        self.assertEqual(df.iloc[0]["title"], "Piso en Getafe")
        self.assertEqual(df.iloc[0]["price"], 180000)
        self.assertEqual(df.iloc[0]["location"], "x")

    def test_detalle_vacio_no_rompe_y_deja_valores_neutros(self):
        pinto = fila(self.df, "https://www.pisos.com/comprar/piso-pinto-4/")
        self.assertEqual(pinto["title"], "Piso en Pinto")
        self.assertEqual(pinto["description"], "")
        self.assertEqual(pinto["location"], "")
        self.assertEqual(list(pinto["features"]), [])
        self.assertEqual(list(pinto["score_details"]), [])
        self.assertEqual(pinto["detail_features"], {})
        self.assertTrue(bool(pinto["cumple_requisitos"]))

    def test_un_valor_nulo_explicito_en_el_detalle_tambien_recibe_el_neutro(self):
        df = api_datos.listings_a_dataframe([listing_api(detalle={"description": None})])
        self.assertEqual(df.iloc[0]["description"], "")

    def test_los_nulos_de_la_api_se_traducen_como_en_los_json_antiguos(self):
        # Antes: 0 cuando faltaba precio, m2, habitaciones, baños o score; app.py hace int() sobre ellos.
        illescas = fila(self.df, "https://www.pisos.com/comprar/piso-illescas-3/")
        self.assertEqual(illescas["m2"], 0)
        self.assertEqual(illescas["score"], 0)
        self.assertTrue(bool(illescas["datos_insuficientes"]))  # la marca real de "sin valorar"
        # lo que en los JSON era null sigue siendo NaN
        self.assertTrue(math.isnan(illescas["price_drop"]))
        self.assertTrue(math.isnan(illescas["previous_price"]))

    def test_precio_habitaciones_y_banos_ausentes_tambien_son_cero(self):
        df = api_datos.listings_a_dataframe(
            [listing_api(precio=None, habitaciones=None, banos=None)]
        )
        r = df.iloc[0]
        self.assertEqual((r["price"], r["rooms"], r["bathrooms"]), (0, 0, 0))

    def test_eur_m2_se_recalcula_como_precio_entre_m2(self):
        self.assertEqual(self.getafe["eur_m2"], round(180000 / 80))
        illescas = fila(self.df, "https://www.pisos.com/comprar/piso-illescas-3/")
        self.assertTrue(math.isnan(illescas["eur_m2"]))  # m2 = 0 no es fiable: NaN, nunca inf

    def test_orden_por_score_descendente(self):
        scores = list(self.df["score"])
        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertEqual(scores[-1], 0)

    def test_lista_vacia_devuelve_dataframe_vacio(self):
        self.assertTrue(api_datos.listings_a_dataframe([]).empty)


class HistoricoADataframeTests(unittest.TestCase):
    """T005 — traducción de /historico."""

    def test_mapea_columnas_y_ordena_por_fecha(self):
        filas = list(reversed(historico_de_ejemplo()))
        df = api_datos.historico_a_dataframe(filas)
        self.assertEqual(
            [c for c in ("fecha", "count", "avg_score", "avg_price", "min_price", "max_price")],
            [c for c in df.columns if c in ("fecha", "count", "avg_score", "avg_price", "min_price", "max_price")],
        )
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(df["fecha"]))
        self.assertEqual(list(df["fecha"]), sorted(df["fecha"]))
        ultimo = df.iloc[-1]
        self.assertEqual(ultimo["count"], 433)
        self.assertEqual(ultimo["avg_score"], 11.48)
        self.assertEqual(ultimo["avg_price"], 224444)
        self.assertEqual(ultimo["min_price"], 29000)
        self.assertEqual(ultimo["max_price"], 700000)

    def test_lista_vacia_devuelve_dataframe_vacio(self):
        self.assertTrue(api_datos.historico_a_dataframe([]).empty)


class ObtenerTests(unittest.TestCase):
    """T006 — peticiones a la API (falsa, pero HTTP real)."""

    def test_obtener_listings_pide_incluir_retirados_y_traduce(self):
        with FakeApi() as api:
            df = api_datos.obtener_listings(api.url)
            self.assertEqual(api.peticiones, ["/listings?incluir_retirados=true"])
        self.assertEqual(len(df), 4)
        self.assertIn("title", df.columns)
        self.assertEqual(set(df["status"]), {"active", "delisted"})

    def test_obtener_historico_pide_historico_y_traduce(self):
        with FakeApi() as api:
            df = api_datos.obtener_historico(api.url)
            self.assertEqual(api.peticiones, ["/historico"])
        self.assertEqual(len(df), 3)
        self.assertIn("avg_score", df.columns)


class ErroresDeRedTests(unittest.TestCase):
    """T012 — cualquier fallo se convierte en ApiNoDisponible con un mensaje claro."""

    def assertNoDisponible(self, funcion, url, mensaje):
        with self.assertRaises(api_datos.ApiNoDisponible) as cm:
            funcion(url)
        self.assertEqual(cm.exception.mensaje, mensaje)
        self.assertTrue(cm.exception.url.startswith(url))
        self.assertIn(url, str(cm.exception))

    def test_conexion_rechazada(self):
        url = f"http://127.0.0.1:{puerto_sin_servidor()}"
        self.assertNoDisponible(
            api_datos.obtener_listings, url, "No se puede conectar con la API"
        )
        self.assertNoDisponible(
            api_datos.obtener_historico, url, "No se puede conectar con la API"
        )

    def test_tiempo_agotado(self):
        with FakeApi() as api:
            api.retardo = 1.5
            with mock.patch.object(api_datos, "_TIMEOUT", (1, 0.3)):
                self.assertNoDisponible(
                    api_datos.obtener_listings, api.url, "La API no ha respondido a tiempo"
                )

    def test_429_no_se_reintenta(self):
        with FakeApi() as api:
            api.estado["/listings"] = 429
            self.assertNoDisponible(
                api_datos.obtener_listings,
                api.url,
                "La API ha limitado las peticiones; espera un momento y recarga",
            )
            self.assertEqual(len(api.peticiones), 1)

    def test_error_http_del_servidor(self):
        with FakeApi() as api:
            api.estado["/listings"] = 500
            api.estado["/historico"] = 503
            self.assertNoDisponible(
                api_datos.obtener_listings, api.url, "La API ha devuelto un error (HTTP 500)"
            )
            self.assertNoDisponible(
                api_datos.obtener_historico, api.url, "La API ha devuelto un error (HTTP 503)"
            )
            self.assertEqual(len(api.peticiones), 2)

    def test_cuerpo_que_no_es_json(self):
        with FakeApi() as api:
            api.cuerpo_crudo["/listings"] = b"esto no es json"
            self.assertNoDisponible(
                api_datos.obtener_listings, api.url, "La respuesta de la API no es válida"
            )

    def test_json_que_no_es_una_lista(self):
        with FakeApi() as api:
            api.cuerpo_crudo["/listings"] = b'{"detail": "otra cosa"}'
            api.cuerpo_crudo["/historico"] = b"[1, 2, 3]"
            self.assertNoDisponible(
                api_datos.obtener_listings, api.url, "La respuesta de la API no es válida"
            )
            self.assertNoDisponible(
                api_datos.obtener_historico, api.url, "La respuesta de la API no es válida"
            )

    def test_una_lista_vacia_no_es_un_error(self):
        with FakeApi(listings=[], historico=[]) as api:
            self.assertTrue(api_datos.obtener_listings(api.url).empty)
            self.assertTrue(api_datos.obtener_historico(api.url).empty)


class DireccionConfigurableTests(unittest.TestCase):
    """T017 — la dirección de la API sale de HOUSESCORE_API_URL (se lee en cada llamada)."""

    def test_sin_variable_se_usa_la_direccion_local(self):
        with mock.patch.dict(os.environ):
            os.environ.pop("HOUSESCORE_API_URL", None)
            self.assertEqual(api_datos.url_api(), "http://localhost:8000")

    def test_con_variable_se_consulta_esa_direccion(self):
        with FakeApi() as api, mock.patch.dict(os.environ, {"HOUSESCORE_API_URL": api.url}):
            df = api_datos.obtener_listings()  # sin argumento: usa la variable
            self.assertEqual(len(df), 4)
            self.assertEqual(api.peticiones, ["/listings?incluir_retirados=true"])

    def test_la_variable_se_lee_en_cada_llamada_no_al_importar(self):
        with FakeApi() as a, FakeApi() as b:
            with mock.patch.dict(os.environ, {"HOUSESCORE_API_URL": a.url}):
                api_datos.obtener_historico()
            with mock.patch.dict(os.environ, {"HOUSESCORE_API_URL": b.url}):
                api_datos.obtener_historico()
            self.assertEqual(len(a.peticiones), 1)
            self.assertEqual(len(b.peticiones), 1)

    def test_el_argumento_tiene_prioridad_y_se_ignora_la_barra_final(self):
        with mock.patch.dict(os.environ, {"HOUSESCORE_API_URL": "http://otra:1"}):
            self.assertEqual(api_datos.url_api("http://x:9/"), "http://x:9")

    def test_el_aviso_de_error_menciona_la_direccion_configurada(self):
        url = f"http://127.0.0.1:{puerto_sin_servidor()}"
        with mock.patch.dict(os.environ, {"HOUSESCORE_API_URL": url}):
            with self.assertRaises(api_datos.ApiNoDisponible) as cm:
                api_datos.obtener_listings()
        self.assertIn(url, cm.exception.url)


if __name__ == "__main__":
    unittest.main()
