# tests/test_db_components.py
# -*- coding: utf-8 -*-

import unittest
import sqlite3

from db import db_schema
from db.analisis import Analisis
from db.paciente import Paciente
from db.hematologia import Hematologia
from db.bioquimica import Bioquimica
from db.gasometria import Gasometria
from db.orina import Orina


class BaseDBTestCase(unittest.TestCase):
    """
    Caso base: crea una BD SQLite en memoria, aplica el esquema
    y construye todos los componentes.
    """

    def setUp(self):
        # BD en memoria
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")

        # Esquema
        cur = self.conn.cursor()
        db_schema.create_schema(cur)
        self.conn.commit()

        # Componentes
        self.analisis = Analisis(self.conn)
        self.paciente = Paciente(self.conn)
        self.hematologia = Hematologia(self.conn, self.analisis)
        self.bioquimica = Bioquimica(self.conn, self.analisis)
        self.gasometria = Gasometria(self.conn, self.analisis)
        self.orina = Orina(self.conn, self.analisis)

    def tearDown(self):
        self.conn.close()


# ---------------------------
#   Analisis
# ---------------------------

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
        data = {
            "fecha_analisis": "2025-11-24",
            "numero_peticion": "PET-002",
            "origen": "GASOMETRIA",
        }
        new_id = self.analisis.create(data)

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


# ---------------------------
#   Paciente
# ---------------------------

class TestPaciente(BaseDBTestCase):
    def test_save_and_get_patient(self):
        info = {
            "nombre": "Borja",
            "apellidos": "Alonso Tristán",
            "fecha_nacimiento": "1985-06-15",
            "sexo": "M",
            "numero_historia": "HIST-123",
        }
        self.paciente.save(info)

        row = self.paciente.get()
        self.assertIsNotNone(row)
        self.assertEqual(row["nombre"], "Borja")
        self.assertEqual(row["apellidos"], "Alonso Tristán")
        self.assertEqual(row["numero_historia"], "HIST-123")

    def test_save_overwrites_previous_patient(self):
        self.paciente.save(
            {
                "nombre": "Paciente1",
                "apellidos": "Uno",
                "fecha_nacimiento": "1990-01-01",
                "sexo": "M",
                "numero_historia": "H1",
            }
        )
        self.paciente.save(
            {
                "nombre": "Paciente2",
                "apellidos": "Dos",
                "fecha_nacimiento": "1995-02-02",
                "sexo": "F",
                "numero_historia": "H2",
            }
        )

        row = self.paciente.get()
        self.assertIsNotNone(row)
        self.assertEqual(row["nombre"], "Paciente2")
        self.assertEqual(row["numero_historia"], "H2")


# ---------------------------
#   Hematologia
# ---------------------------

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

        # campos de hematologia
        self.assertAlmostEqual(row["leucocitos"], 5.2)
        self.assertAlmostEqual(row["hemoglobina"], 13.5)
        self.assertAlmostEqual(row["plaquetas"], 250)

        # campos heredados de analisis
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


# ---------------------------
#   Bioquimica
# ---------------------------

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


# ---------------------------
#   Gasometria
# ---------------------------

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


# ---------------------------
#   Orina
# ---------------------------

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
