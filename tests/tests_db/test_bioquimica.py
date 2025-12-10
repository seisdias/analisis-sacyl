# tests/db/test_bioquimica.py

from .base import BaseDBTestCase


class TestBioquimica(BaseDBTestCase):
    def test_insert_and_list(self):
        data = {
            "fecha_analisis": "2025-11-24",
            "numero_peticion": "BIO-001",
            "origen": "BIO",
            "glucosa": 90,
            "urea": 30,
            "creatinina": 0.9,
        }
        self.bioquimica.insert(data)

        rows = self.bioquimica.list()
        self.assertEqual(len(rows), 1)
        row = rows[0]

        self.assertAlmostEqual(row["glucosa"], 90)
        self.assertAlmostEqual(row["urea"], 30)
        self.assertAlmostEqual(row["creatinina"], 0.9)
        self.assertEqual(row["fecha_analisis"], "2025-11-24")
        self.assertEqual(row["numero_peticion"], "BIO-001")
        self.assertEqual(row["origen"], "BIO")
