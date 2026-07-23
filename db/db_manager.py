# db/db_manager.py
# -*- coding: utf-8 -*-

import sqlite3
from pathlib import Path
from typing import Dict, Any, Optional

from .analisis import Analisis
from .config import Config
from .ingreso import Ingreso
from .limite_parametro import LimiteParametro
from .paciente import Paciente
from .hematologia import Hematologia
from .bioquimica import Bioquimica
from .gasometria import Gasometria
from .orina import Orina
from .tratamiento import Tratamiento
from .schema_migrations import create_database, prepare_database, sqlite_rw_uri

DB_FILE = "analisis.db"


class AnalysisDB:
    """
    Fachada principal para la base de datos de análisis clínicos.

    Contiene componentes:
      - analisis (cabecera del documento)
      - paciente
      - hematologia
      - bioquimica
      - gasometria
      - orina
    """

    def __init__(self, db_path: str = DB_FILE):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self.is_open: bool = False

        # Componentes
        self.analisis: Optional[Analisis] = None
        self.paciente: Optional[Paciente] = None
        self.hematologia: Optional[Hematologia] = None
        self.bioquimica: Optional[Bioquimica] = None
        self.gasometria: Optional[Gasometria] = None
        self.orina: Optional[Orina] = None
        self.config: Optional[Config] = None
        self.limite_parametro: Optional[LimiteParametro] = None
        self.tratamiento: Optional[Tratamiento] = None
        self.ingreso: Optional[Ingreso] = None

    # --------------------
    #   OPEN / CLOSE
    # --------------------
    def open(self) -> None:
        if self.is_open:
            return
        db_path = Path(self.db_path)
        if not db_path.is_file():
            raise FileNotFoundError(f"La base de datos no existe: {db_path}")
        try:
            prepare_database(db_path, check_integrity=False)
            self.conn = sqlite3.connect(
                sqlite_rw_uri(db_path.resolve()), uri=True, check_same_thread=False
            )
            self.conn.row_factory = sqlite3.Row
            self.conn.execute("PRAGMA foreign_keys = ON")
            self._init_components()
            self.is_open = True
        except Exception:
            self.close()
            raise

    def create(self) -> None:
        """Initialise a reserved empty file as a formally versioned database."""
        if self.is_open:
            raise RuntimeError("La base de datos ya está abierta")
        create_database(self.db_path)
        self.open()

    def close(self) -> None:
        if self.conn:
            self.conn.close()

        self.conn = None
        self.is_open = False

    def _init_components(self) -> None:
        self.analisis = Analisis(self.conn)
        self.paciente = Paciente(self.conn)
        self.hematologia = Hematologia(self.conn, self.analisis)
        self.bioquimica = Bioquimica(self.conn, self.analisis)
        self.gasometria = Gasometria(self.conn, self.analisis)
        self.orina = Orina(self.conn, self.analisis)
        self.config = Config(self.conn)
        self.limite_parametro = LimiteParametro(self.conn)
        self.tratamiento = Tratamiento(self.conn)
        self.ingreso = Ingreso(self.conn)

    # --------------------
    #   API FACHADA
    # --------------------
    # Analisis
    def create_analisis(self, info: Dict[str, Any], commit: bool = True) -> int:
        return self.analisis.create(info, commit=commit)

    def list_analisis(self, limit: Optional[int] = None):
        return self.analisis.list(limit)

    # Paciente
    def save_patient(self, d: Dict[str, Any], commit: bool = True):
        return self.paciente.save(d, commit=commit)

    def get_patient(self):
        return self.paciente.get()

    # Hematologia
    def insert_hematologia(self, d: Dict[str, Any], commit: bool = True):
        return self.hematologia.insert(d, commit=commit)

    def list_hematologia(self, limit=None):
        return self.hematologia.list(limit)

    # Bioquímica
    def insert_bioquimica(self, d: Dict[str, Any], commit: bool = True):
        return self.bioquimica.insert(d, commit=commit)

    def list_bioquimica(self, limit=None):
        return self.bioquimica.list(limit)

    # Gasometría
    def insert_gasometria(self, d: Dict[str, Any], commit: bool = True):
        return self.gasometria.insert(d, commit=commit)

    def list_gasometria(self, limit=None):
        return self.gasometria.list(limit)

    # Orina
    def insert_orina(self, d: Dict[str, Any], commit: bool = True):
        return self.orina.insert(d, commit=commit)

    def list_orina(self, limit=None):
        return self.orina.list(limit)



