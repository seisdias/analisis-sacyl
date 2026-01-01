import os
import sqlite3
from pathlib import Path

import pytest

from db.db_manager import AnalysisDB


def _table_info(conn: sqlite3.Connection, table: str):
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    # PRAGMA table_info: cid, name, type, notnull, dflt_value, pk
    return [
        {
            "cid": r[0],
            "name": r[1],
            "type": (r[2] or "").upper(),
            "notnull": bool(r[3]),
            "dflt": r[4],
            "pk": bool(r[5]),
        }
        for r in rows
    ]


def _dummy_value(col_type: str):
    t = (col_type or "").upper()
    if "INT" in t:
        return 0
    if any(x in t for x in ("REAL", "FLOA", "DOUB", "NUM")):
        return 0.0
    # TEXT / DATE / DATETIME / etc.
    return ""


def _insert_row_safely(conn: sqlite3.Connection, table: str, values: dict) -> int:
    """
    Inserta una fila de forma robusta:
    - Rellena columnas NOT NULL sin default si no están en `values`.
    - No fuerza PK autoincrement.
    Devuelve lastrowid.
    """
    info = _table_info(conn, table)
    cols = []
    params = []

    for c in info:
        name = c["name"]
        if c["pk"]:
            # no forzar PK autoincrement
            continue

        if name in values:
            cols.append(name)
            params.append(values[name])
            continue

        # si es NOT NULL y no tiene default => rellenar dummy
        if c["notnull"] and c["dflt"] is None:
            cols.append(name)
            params.append(_dummy_value(c["type"]))

    if not cols:
        # tabla sin columnas insertables (raro); intentamos insert default
        cur = conn.execute(f"INSERT INTO {table} DEFAULT VALUES")
        return cur.lastrowid

    placeholders = ",".join(["?"] * len(cols))
    col_list = ",".join(cols)
    cur = conn.execute(
        f"INSERT INTO {table} ({col_list}) VALUES ({placeholders})",
        params,
    )
    return cur.lastrowid


@pytest.mark.parametrize(
    "dates_in, expected_out",
    [
        (["2025-11-10", "2025-11-12", "2025-11-08"], ["2025-11-12", "2025-11-10", "2025-11-08"]),
    ],
)
def test_hematologia_list_distinct_dates_desc_unique(tmp_path: Path, dates_in, expected_out):
    db_path = tmp_path / "test.db"

    db = AnalysisDB(str(db_path))
    db.open()
    try:
        conn = db.conn
        assert conn is not None

        # Insertamos 3 analisis con fechas y 1 hematologia por analisis
        for d in dates_in:
            analisis_id = _insert_row_safely(conn, "analisis", {"fecha_analisis": d})
            _insert_row_safely(conn, "hematologia", {"analisis_id": analisis_id})

        # Insertamos un duplicado de fecha (otro analisis mismo día) para validar DISTINCT
        dup_id = _insert_row_safely(conn, "analisis", {"fecha_analisis": dates_in[0]})
        _insert_row_safely(conn, "hematologia", {"analisis_id": dup_id})

        conn.commit()

        out = db.hematologia.list_distinct_dates()
        assert out == expected_out
        assert len(out) == len(set(out))  # unique
    finally:
        db.close()
