# tests/test_db/test_analysis_db.py
# -*- coding: utf-8 -*-

import os
import tempfile
import unittest

from db import AnalysisDB


class TestAnalysisDB(unittest.TestCase):
    """
    Tests de integración de la fachada AnalysisDB.
    Comprueban que los componentes internos se coordinan bien
    y que la API pública funciona como se espera.
    """

    def setUp(self):
        # Usamos un fichero temporal para probar también el path
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "test_analisis.db")
        self.db = AnalysisDB(db_path=self.db_path)
        self.db.open()

    def tearDown(self):
        self.db.close()
        self.tmp_dir.cleanup()

    # ------------------------------------------------------------------
    #   ANALISIS: crear y listar
    # ------------------------------------------------------------------
    def test_create_and_list_analisis(self):
        a1_id = self.db.create_analisis(
            {
                "fecha_analisis": "2025-11-24",
                "numero_peticion": "PET-001",
                "origen": "HEMATOLOGIA",
            }
        )
        a2_id = self.db.create_analisis(
            {
                "fecha_analisis": "2025-11-25",
                "numero_peticion": "PET-002",
                "origen": "BIOQUIMICA",
            }
        )

        analisis_list = self.db.list_analisis()
        self.assertEqual(len(analisis_list), 2)

        ids = {row["id"] for row in analisis_list}
        self.assertIn(a1_id, ids)
        self.assertIn(a2_id, ids)

    # ------------------------------------------------------------------
    #   PACIENTE + HEMATOLOGÍA (flujo básico)
    # ------------------------------------------------------------------
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

        # Insertar hematología (crea analisis automáticamente)
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

    # ------------------------------------------------------------------
    #   Varias secciones compartiendo el MISMO analisis_id
    # ------------------------------------------------------------------
    def test_shared_analisis_between_sections(self):
        """
        Comprueba que hematología, bioquímica, gasometría y orina
        pueden colgar del mismo análisis y heredan fecha/nº petición/origen.
        """
        analisis_id = self.db.create_analisis(
            {
                "fecha_analisis": "2025-11-28",
                "numero_peticion": "MIX-001",
                "origen": "CONSULTA",
            }
        )

        # Hematología
        self.db.insert_hematologia(
            {
                "analisis_id": analisis_id,
                "leucocitos": 5.0,
            }
        )

        # Bioquímica
        self.db.insert_bioquimica(
            {
                "analisis_id": analisis_id,
                "glucosa": 95.0,
            }
        )

        # Gasometría
        self.db.insert_gasometria(
            {
                "analisis_id": analisis_id,
                "gaso_ph": 7.40,
            }
        )

        # Orina
        self.db.insert_orina(
            {
                "analisis_id": analisis_id,
                "ph": 6.0,
            }
        )

        hem = self.db.list_hematologia()[0]
        bio = self.db.list_bioquimica()[0]
        gas = self.db.list_gasometria()[0]
        ori = self.db.list_orina()[0]

        # Todos deben compartir cabecera de analisis
        for row in (hem, bio, gas, ori):
            self.assertEqual(row["fecha_analisis"], "2025-11-28")
            self.assertEqual(row["numero_peticion"], "MIX-001")
            self.assertEqual(row["origen"], "CONSULTA")

    # ------------------------------------------------------------------
    #   Inserciones con creación automática de analisis (ensure)
    # ------------------------------------------------------------------
    def test_auto_analisis_creation_via_insert_sections(self):
        """
        Si insertamos secciones sin analisis_id pero con fecha/numero_peticion/origen,
        Analisis.ensure creará entradas nuevas. Verificamos que se crean.
        """
        self.db.insert_hematologia(
            {
                "fecha_analisis": "2025-12-01",
                "numero_peticion": "AUTO-001",
                "origen": "AUTO",
                "leucocitos": 6.0,
            }
        )
        self.db.insert_bioquimica(
            {
                "fecha_analisis": "2025-12-02",
                "numero_peticion": "AUTO-002",
                "origen": "AUTO",
                "glucosa": 100.0,
            }
        )

        analisis_list = self.db.list_analisis()
        # Habrá al menos 2 analisis (uno por cada ensure)
        self.assertGreaterEqual(len(analisis_list), 2)

        # Y las secciones tendrán sus cabeceras correctas
        hem = self.db.list_hematologia()[0]
        bio = self.db.list_bioquimica()[0]

        self.assertEqual(hem["numero_peticion"], "AUTO-001")
        self.assertEqual(bio["numero_peticion"], "AUTO-002")

    # ------------------------------------------------------------------
    #   Parámetro limit en list_*
    # ------------------------------------------------------------------
    def test_limit_parameter_on_lists(self):
        # Insertamos 3 análisis de hematología
        for i in range(3):
            self.db.insert_hematologia(
                {
                    "fecha_analisis": f"2025-11-2{i}",
                    "numero_peticion": f"HEM-LIM-{i}",
                    "origen": "LIMIT",
                    "leucocitos": 4.0 + i,
                }
            )

        all_rows = self.db.list_hematologia()
        limited_rows = self.db.list_hematologia(limit=2)

        self.assertEqual(len(all_rows), 3)
        self.assertEqual(len(limited_rows), 2)

        # También probamos el limit en list_analisis
        all_analisis = self.db.list_analisis()
        limited_analisis = self.db.list_analisis(limit=1)

        self.assertGreaterEqual(len(all_analisis), 3)
        self.assertEqual(len(limited_analisis), 1)

    # ------------------------------------------------------------------
    #   ERRORES ESPERADOS: crear analisis sin fecha_analisis
    # ------------------------------------------------------------------
    def test_create_analisis_without_fecha_raises(self):
        """
        Analisis.create requiere fecha_analisis.
        AnalysisDB.create_analisis delega en él, así que debe lanzar ValueError.
        """
        with self.assertRaises(ValueError):
            self.db.create_analisis(
                {
                    # "fecha_analisis" falta a propósito
                    "numero_peticion": "NO-FECHA",
                    "origen": "TEST",
                }
            )

    # ------------------------------------------------------------------
    #   ERRORES ESPERADOS: insertar sección sin analisis_id ni fecha
    # ------------------------------------------------------------------
    def test_insert_hematologia_without_analisis_nor_fecha_raises(self):
        """
        Analisis.ensure exige analisis_id o fecha_analisis.
        Si llamamos a insert_hematologia sin ninguno de los dos,
        debe lanzar ValueError.
        """
        with self.assertRaises(ValueError):
            self.db.insert_hematologia(
                {
                    # faltan analisis_id y fecha_analisis
                    "leucocitos": 5.0,
                }
            )

    # ------------------------------------------------------------------
    #   ON DELETE CASCADE: borrar un analisis elimina sus secciones
    # ------------------------------------------------------------------
    def test_delete_analisis_cascades_to_sections(self):
        """
        Verifica que la FK con ON DELETE CASCADE funciona:
        al borrar una fila de analisis, se eliminan sus hematologia/bioquimica/etc.
        """
        # Creamos un analisis y colgamos todas las secciones de él
        analisis_id = self.db.create_analisis(
            {
                "fecha_analisis": "2025-12-05",
                "numero_peticion": "CASCADE-001",
                "origen": "HOSPITAL",
            }
        )

        self.db.insert_hematologia(
            {
                "analisis_id": analisis_id,
                "leucocitos": 4.5,
            }
        )
        self.db.insert_bioquimica(
            {
                "analisis_id": analisis_id,
                "glucosa": 88.0,
            }
        )
        self.db.insert_gasometria(
            {
                "analisis_id": analisis_id,
                "gaso_ph": 7.41,
            }
        )
        self.db.insert_orina(
            {
                "analisis_id": analisis_id,
                "ph": 6.0,
            }
        )

        # Comprobamos que están insertadas
        self.assertEqual(len(self.db.list_hematologia()), 1)
        self.assertEqual(len(self.db.list_bioquimica()), 1)
        self.assertEqual(len(self.db.list_gasometria()), 1)
        self.assertEqual(len(self.db.list_orina()), 1)

        # Borramos la cabecera de analisis directamente
        self.db.conn.execute("DELETE FROM analisis WHERE id = ?", (analisis_id,))
        self.db.conn.commit()

        # Ahora todas las secciones deben estar vacías
        self.assertEqual(len(self.db.list_hematologia()), 0)
        self.assertEqual(len(self.db.list_bioquimica()), 0)
        self.assertEqual(len(self.db.list_gasometria()), 0)
        self.assertEqual(len(self.db.list_orina()), 0)


if __name__ == "__main__":
    unittest.main()
