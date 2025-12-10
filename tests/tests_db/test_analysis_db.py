# tests/db/test_analysis_db.py
# -*- coding: utf-8 -*-

import os
import tempfile
import unittest

from db import AnalysisDB


class TestAnalysisDB(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "test_analisis.db")
        self.db = AnalysisDB(db_path=self.db_path)
        self.db.open()

    def tearDown(self):
        self.db.close()
        self.tmp_dir.cleanup()

    def test_patient_and_hematologia_flow(self):
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
