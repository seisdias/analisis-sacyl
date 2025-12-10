# tests/db/base.py
# -*- coding: utf-8 -*-

import sqlite3
import unittest

from db import db_schema
from db.analisis import Analisis
from db.paciente import Paciente
from db.hematologia import Hematologia
from db.bioquimica import Bioquimica
from db.gasometria import Gasometria
from db.orina import Orina


class BaseDBTestCase(unittest.TestCase):
    """
    Caso base: crea una BD en memoria, aplica el esquema y
    construye todos los componentes de db.
    """

    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")

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
