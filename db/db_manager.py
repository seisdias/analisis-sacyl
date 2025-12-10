# db/db_manager.py
# -*- coding: utf-8 -*-

import sqlite3
from typing import Dict, Any, List, Optional

from . import db_schema
from .analisis import Analisis
from .paciente import Paciente
from .hematologia import Hematologia
from .bioquimica import Bioquimica
from .gasometria import Gasometria
from .orina import Orina

DB_FILE = "hematologia.db"


class HematologyDB:
    """
    Fachada principal para la base de datos de análisis de laboratorio.
    """

    def __init__(self, db_path: str = DB_FILE):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self.is_open: bool = False

        self.analisis: Optional[Analisis] = None
        self.paciente: Optional[Paciente] = None
        self.hematologia: Optional[Hematologia] = None
        self.bioquimica: Optional[Bioquimica] = None
        self.gasometria: Optional[Gasometria] = None
        self.orina: Optional[Orina] = None

    # --------------------
    #   OPEN / CLOSE
    # --------------------
    def open(self) -> None:
        if self.is_open:
            return

        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")

        self._create_tables()
        self._init_components()
        self.is_open = True

    def close(self) -> None:
        if self.conn and self.is_open:
            self.conn.close()
        self.conn = None
        self.is_open = False

        self.analisis = None
        self.paciente = None
        self.hematologia = None
        self.bioquimica = None
        self.gasometria = None
        self.orina = None

    # --------------------
    #   INIT
    # --------------------
    def _create_tables(self) -> None:
        if not self.conn:
            raise RuntimeError("Conexión no inicializada.")
        cur = self.conn.cursor()
        db_schema.create_schema(cur)
        self.conn.commit()

    def _init_components(self) -> None:
        if not self.conn:
            raise RuntimeError("Conexión no inicializada.")

        self.analisis = Analisis(self.conn)
        self.paciente = Paciente(self.conn)
        self.hematologia = Hematologia(self.conn, self.analisis)
        self.bioquimica = Bioquimica(self.conn, self.analisis)
        self.gasometria = Gasometria(self.conn, self.analisis)
        self.orina = Orina(self.conn, self.analisis)

    # --------------------
    #   API FACHADA
    # --------------------
    # Analisis
    def create_analisis(self, info: Dict[str, Any]) -> int:
        return self.analisis.create(info)

    def list_analisis(self, limit: Optional[int] = None):
        return self.analisis.list(limit)

    # Paciente
    def save_patient(self, d: Dict[str, Any]) -> None:
        self.paciente.save(d)

    def get_patient(self):
        return self.paciente.get()

    # Hematologia
    def insert_hematologia(self, d: Dict[str, Any]) -> None:
        self.hematologia.insert(d)

    def list_hematologia(self, limit: Optional[int] = None):
        return self.hematologia.list(limit)

    # Bioquimica
    def insert_bioquimica(self, d: Dict[str, Any]) -> None:
        self.bioquimica.insert(d)

    def list_bioquimica(self, limit: Optional[int] = None):
        return self.bioquimica.list(limit)

    # Gasometria
    def insert_gasometria(self, d: Dict[str, Any]) -> None:
        self.gasometria.insert(d)

    def list_gasometria(self, limit: Optional[int] = None):
        return self.gasometria.list(limit)

    # Orina
    def insert_orina(self, d: Dict[str, Any]) -> None:
        self.orina.insert(d)

    def list_orina(self, limit: Optional[int] = None):
        return self.orina.list(limit)
