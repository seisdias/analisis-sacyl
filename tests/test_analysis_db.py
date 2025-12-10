# tests/test_analysis_db.py
# -*- coding: utf-8 -*-

import unittest
import os
import tempfile

from db import AnalysisDB


class TestAnalysisDB(unittest.TestCase):
    def setUp(self):
        # BD en fichero temporal (para probar el path)
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "test_analisis.db")
        self.db = AnalysisDB(db_path=self.db_path)
        self.db.open()

    def tearDown(self):
        self.db.close()
        self.tmp_dir.cleanup()

    def test_patient_and_hematologia_flow(self):
        # Guardar paciente
        self.db.save_patient(
            {
                "nombre": "Borja",
                "apellidos": "Alonso Tristán",
                "fecha_nacimiento": "1985-06-15",
                "sexo": "M",
                "numero_historia": "HIST-999",
            }
        )
        paciente = self.db.get_patient()
        self.assertIsNotNone(paciente)
        self.assertEqual(paciente["numero_historia"], "HIST-999")

        # Insertar hematología
        self.db.insert_hematologia(
            {
                "fecha_analisis": "2025-11-27",
                "numero_peticion": "HEM-999",
                "origen": "HOSPITAL",
                "leucocitos": 4.8,
                "hemoglobina": 14.0,
                "plaquetas": 230,
            }
        )

        rows = self.db.list_hematologia()
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["numero_peticion"], "HEM-999")
        self.assertAlmostEqual(row["leucocitos"], 4.8)

    def test_shared_analisis_between_sections(self):
        """
        Comprueba que varias secciones (ej. hematología y bioquímica)
        pueden colgar del mismo analisis.
        """
        # Creamos primero un analisis explícito
        analisis_id = self.db.create_analisis(
            {
                "fecha_analisis": "2025-11-28",
                "numero_peticion": "MIX-001",
                "origen": "CONSULTA",
            }
        )

        # Insertar hematología y bioquímica usando ese analisis_id
        self.db.insert_hematologia(
            {
                "analisis_id": analisis_id,
                "leucocitos": 5.0,
            }
        )
        self.db.insert_bioquimica(
            {
                "analisis_id": analisis_id,
                "glucosa": 95,
            }
        )

        hem_rows = self.db.list_hematologia()
        bio_rows = self.db.list_bioquimica()
        self.assertEqual(len(hem_rows), 1)
        self.assertEqual(len(bio_rows), 1)

        # Ambos deberían tener misma fecha / número_petición / origen
        self.assertEqual(hem_rows[0]["fecha_analisis"], "2025-11-28")
        self.assertEqual(bio_rows[0]["fecha_analisis"], "2025-11-28")
        self.assertEqual(hem_rows[0]["numero_peticion"], "MIX-001")
        self.assertEqual(bio_rows[0]["numero_peticion"], "MIX-001")


if __name__ == "__main__":
    unittest.main()
