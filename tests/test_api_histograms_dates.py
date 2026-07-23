import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient

from api.server import app
from api.deps import set_db_path
from db.db_manager import AnalysisDB


def _table_info(conn: sqlite3.Connection, table: str):
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return [
        {
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
    return ""


def _insert_row_safely(conn: sqlite3.Connection, table: str, values: dict) -> int:
    info = _table_info(conn, table)
    cols, params = [], []

    for c in info:
        name = c["name"]
        if c["pk"]:
            continue

        if name in values:
            cols.append(name)
            params.append(values[name])
        elif c["notnull"] and c["dflt"] is None:
            cols.append(name)
            params.append(_dummy_value(c["type"]))

    if not cols:
        cur = conn.execute(f"INSERT INTO {table} DEFAULT VALUES")
        return cur.lastrowid

    placeholders = ",".join(["?"] * len(cols))
    cur = conn.execute(
        f"INSERT INTO {table} ({','.join(cols)}) VALUES ({placeholders})",
        params,
    )
    return cur.lastrowid


def test_api_histograms_dates_returns_dates(tmp_path: Path):
    db_path = tmp_path / "api_test.db"

    # Crear DB + schema
    db = AnalysisDB(str(db_path))
    db.create()
    try:
        conn = db.conn
        assert conn is not None

        # Datos: 2 fechas
        a1 = _insert_row_safely(conn, "analisis", {"fecha_analisis": "2025-11-24"})
        _insert_row_safely(conn, "hematologia", {"analisis_id": a1})

        a2 = _insert_row_safely(conn, "analisis", {"fecha_analisis": "2025-11-27"})
        _insert_row_safely(conn, "hematologia", {"analisis_id": a2})

        conn.commit()
    finally:
        db.close()

    # Enlazar app a esta BD en modo legacy (sin session_id)
    set_db_path(app, str(db_path))

    client = TestClient(app)
    r = client.get("/histograms/dates")
    assert r.status_code == 200
    data = r.json()
    assert data["dates"] == ["2025-11-27", "2025-11-24"]
