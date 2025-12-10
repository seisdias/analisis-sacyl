# tests/db/test_gasometria.py

from .base import BaseDBTestCase


class TestGasometria(BaseDBTestCase):
    def test_insert_and_list(self):
        data = {
            "fecha_analisis": "2025-11-24",
            "numero_peticion": "GASO-001",
            "origen": "GASO",
            "gaso_ph": 7.40,
            "gaso_pco2": 40,
            "gaso_po2": 95,
        }
        self.gasometria.insert(data)

        rows = self.gasometria.list()
        self.assertEqual(len(rows), 1)
        row = rows[0]

        self.assertAlmostEqual(row["gaso_ph"], 7.40)
        self.assertAlmostEqual(row["gaso_pco2"], 40)
        self.assertAlmostEqual(row["gaso_po2"], 95)
        self.assertEqual(row["fecha_analisis"], "2025-11-24")
        self.assertEqual(row["numero_peticion"], "GASO-001")
        self.assertEqual(row["origen"], "GASO")
