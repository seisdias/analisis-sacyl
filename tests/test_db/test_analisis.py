# tests/db/test_analisis.py

from .base import BaseDBTestCase


class TestAnalisis(BaseDBTestCase):
    def test_create_and_list_single(self):
        data = {
            "fecha_analisis": "2025-11-24",
            "numero_peticion": "PET-001",
            "origen": "HEMATOLOGIA",
        }
        new_id = self.analisis.create(data)
        self.assertIsInstance(new_id, int)

        rows = self.analisis.list()
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["id"], new_id)
        self.assertEqual(row["fecha_analisis"], "2025-11-24")
        self.assertEqual(row["numero_peticion"], "PET-001")
        self.assertEqual(row["origen"], "HEMATOLOGIA")

    def test_ensure_with_existing_id(self):
        new_id = self.analisis.create(
            {
                "fecha_analisis": "2025-11-24",
                "numero_peticion": "PET-002",
                "origen": "GASOMETRIA",
            }
        )
        ensured_id = self.analisis.ensure({"analisis_id": new_id})
        self.assertEqual(ensured_id, new_id)

    def test_ensure_creates_when_no_id_but_fecha(self):
        ensured_id = self.analisis.ensure(
            {
                "fecha_analisis": "2025-11-25",
                "numero_peticion": "PET-003",
                "origen": "BIOQUIMICA",
            }
        )
        self.assertIsInstance(ensured_id, int)
        rows = self.analisis.list()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["id"], ensured_id)
