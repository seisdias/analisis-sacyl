# tests/db/test_hematologia.py

from .base import BaseDBTestCase


class TestHematologia(BaseDBTestCase):
    def test_insert_and_list(self):
        data = {
            "fecha_analisis": "2025-11-24",
            "numero_peticion": "PET-100",
            "origen": "HEM",
            "leucocitos": 5.2,
            "hemoglobina": 13.5,
            "plaquetas": 250,
        }
        self.hematologia.insert(data)

        rows = self.hematologia.list()
        self.assertEqual(len(rows), 1)
        row = rows[0]

        self.assertAlmostEqual(row["leucocitos"], 5.2)
        self.assertAlmostEqual(row["hemoglobina"], 13.5)
        self.assertAlmostEqual(row["plaquetas"], 250)
        self.assertEqual(row["fecha_analisis"], "2025-11-24")
        self.assertEqual(row["numero_peticion"], "PET-100")
        self.assertEqual(row["origen"], "HEM")

    def test_limit_in_list(self):
        for i in range(3):
            self.hematologia.insert(
                {
                    "fecha_analisis": f"2025-11-2{i}",
                    "numero_peticion": f"PET-{i}",
                    "origen": "HEM",
                    "leucocitos": 4.0 + i,
                }
            )

        rows_all = self.hematologia.list()
        rows_lim = self.hematologia.list(limit=2)

        self.assertEqual(len(rows_all), 3)
        self.assertEqual(len(rows_lim), 2)
