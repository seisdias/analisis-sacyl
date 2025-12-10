# tests/db/test_orina.py

from .base import BaseDBTestCase


class TestOrina(BaseDBTestCase):
    def test_insert_and_list(self):
        data = {
            "fecha_analisis": "2025-11-24",
            "numero_peticion": "ORINA-001",
            "origen": "ORINA",
            "ph": 6.0,
            "densidad": 1.020,
            "glucosa": "NEG",
            "proteinas": "NEG",
            "sangre": "POS",
        }
        self.orina.insert(data)

        rows = self.orina.list()
        self.assertEqual(len(rows), 1)
        row = rows[0]

        self.assertAlmostEqual(row["ph"], 6.0)
        self.assertAlmostEqual(row["densidad"], 1.020)
        self.assertEqual(row["glucosa"], "NEG")
        self.assertEqual(row["proteinas"], "NEG")
        self.assertEqual(row["sangre"], "POS")
        self.assertEqual(row["fecha_analisis"], "2025-11-24")
        self.assertEqual(row["numero_peticion"], "ORINA-001")
        self.assertEqual(row["origen"], "ORINA")
