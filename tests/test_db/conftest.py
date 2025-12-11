# tests/test_db/conftest.py
# -*- coding: utf-8 -*-

import os
import sqlite3
import tempfile

import pytest

from db import db_schema, AnalysisDB
from db.analisis import Analisis
from db.paciente import Paciente
from db.hematologia import Hematologia
from db.bioquimica import Bioquimica
from db.gasometria import Gasometria
from db.orina import Orina


@pytest.fixture
def sqlite_conn():
    """
    Conexión SQLite en memoria con el esquema creado.
    Equivalente al setUp de BaseDBTestCase.
    """
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()
    db_schema.create_schema(cur)
    conn.commit()
    try:
        yield conn
    finally:
        conn.close()


@pytest.fixture
def components(sqlite_conn):
    """
    Devuelve todos los componentes de db construidos
    sobre la misma conexión.
    """
    analisis = Analisis(sqlite_conn)
    paciente = Paciente(sqlite_conn)
    hematologia = Hematologia(sqlite_conn, analisis)
    bioquimica = Bioquimica(sqlite_conn, analisis)
    gasometria = Gasometria(sqlite_conn, analisis)
    orina = Orina(sqlite_conn, analisis)

    return {
        "conn": sqlite_conn,
        "analisis": analisis,
        "paciente": paciente,
        "hematologia": hematologia,
        "bioquimica": bioquimica,
        "gasometria": gasometria,
        "orina": orina,
    }


@pytest.fixture
def analysis_db(tmp_path):
    """
    Fixture para AnalysisDB usando un fichero temporal.
    Sustituye al setUp/tearDown de TestAnalysisDB.
    """
    db_path = os.path.join(tmp_path, "test_analisis.db")
    db = AnalysisDB(db_path=db_path)
    db.open()
    try:
        yield db
    finally:
        db.close()
