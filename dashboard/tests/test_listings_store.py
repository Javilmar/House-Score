import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import listings_store


class UpsertTests(unittest.TestCase):
    def test_nuevo_piso_se_anade_con_first_seen_y_last_seen_hoy(self):
        today = "2026-07-14"
        nuevo = {"url": "https://a.com/1", "price": 200000}

        index = listings_store.upsert({}, [nuevo], today)

        item = index["https://a.com/1"]
        self.assertEqual(item["first_seen"], today)
        self.assertEqual(item["last_seen"], today)
        self.assertEqual(item["status"], "active")

    def test_piso_existente_conserva_first_seen_y_actualiza_last_seen(self):
        existing = {
            "https://a.com/1": {
                "url": "https://a.com/1",
                "price": 200000,
                "first_seen": "2026-07-01",
                "last_seen": "2026-07-10",
                "status": "active",
            }
        }
        visto_hoy = {"url": "https://a.com/1", "price": 200000}

        index = listings_store.upsert(existing, [visto_hoy], "2026-07-14")

        item = index["https://a.com/1"]
        self.assertEqual(item["first_seen"], "2026-07-01")
        self.assertEqual(item["last_seen"], "2026-07-14")

    def test_bajada_de_precio_se_registra(self):
        existing = {
            "https://a.com/1": {
                "url": "https://a.com/1",
                "price": 200000,
                "first_seen": "2026-07-01",
                "last_seen": "2026-07-10",
                "status": "active",
            }
        }
        bajado = {"url": "https://a.com/1", "price": 180000}

        index = listings_store.upsert(existing, [bajado], "2026-07-14")

        item = index["https://a.com/1"]
        self.assertEqual(item["price_drop"], 20000)
        self.assertEqual(item["previous_price"], 200000)

    def test_piso_delisted_que_reaparece_vuelve_a_activo(self):
        existing = {
            "https://a.com/1": {
                "url": "https://a.com/1",
                "price": 200000,
                "first_seen": "2026-07-01",
                "last_seen": "2026-07-01",
                "status": "delisted",
            }
        }
        reaparece = {"url": "https://a.com/1", "price": 200000}

        index = listings_store.upsert(existing, [reaparece], "2026-07-14")

        self.assertEqual(index["https://a.com/1"]["status"], "active")


class MarkDelistedTests(unittest.TestCase):
    def test_piso_sin_ver_7_dias_pasa_a_delisted(self):
        index = {
            "https://a.com/1": {
                "url": "https://a.com/1",
                "last_seen": "2026-07-07",
                "status": "active",
            }
        }

        result = listings_store.mark_delisted(index, "2026-07-14", threshold_days=7)

        self.assertEqual(result["https://a.com/1"]["status"], "delisted")

    def test_piso_visto_hace_6_dias_sigue_activo(self):
        index = {
            "https://a.com/1": {
                "url": "https://a.com/1",
                "last_seen": "2026-07-08",
                "status": "active",
            }
        }

        result = listings_store.mark_delisted(index, "2026-07-14", threshold_days=7)

        self.assertEqual(result["https://a.com/1"]["status"], "active")


class AppendDailyAggregateTests(unittest.TestCase):
    def test_agrega_una_fila_por_dia(self):
        listings = [
            {"price": 100000, "score": 5.0},
            {"price": 200000, "score": 7.0},
        ]

        historico = listings_store.append_daily_aggregate([], listings, "2026-07-14")

        self.assertEqual(len(historico), 1)
        fila = historico[0]
        self.assertEqual(fila["fecha"], "2026-07-14")
        self.assertEqual(fila["count"], 2)
        self.assertEqual(fila["avg_price"], 150000)
        self.assertEqual(fila["avg_score"], 6.0)
        self.assertEqual(fila["min_price"], 100000)
        self.assertEqual(fila["max_price"], 200000)

    def test_no_duplica_fecha_si_se_ejecuta_dos_veces_el_mismo_dia(self):
        listings = [{"price": 100000, "score": 5.0}]
        historico = listings_store.append_daily_aggregate([], listings, "2026-07-14")

        historico = listings_store.append_daily_aggregate(
            historico, listings, "2026-07-14"
        )

        self.assertEqual(len(historico), 1)


if __name__ == "__main__":
    unittest.main()
