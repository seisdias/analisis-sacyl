# db/paciente.py
# -*- coding: utf-8 -*-

import sqlite3
from typing import Dict, Any, Optional


class Paciente:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def save(self, info: Dict[str, Any]) -> None:
        cur = self.conn.cursor()
        cur.execute("DELETE FROM paciente")
        cur.execute(
            """
            INSERT INTO paciente (nombre, apellidos, fecha_nacimiento, sexo, numero_historia)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                info.get("nombre"),
                info.get("apellidos"),
                info.get("fecha_nacimiento"),
                info.get("sexo"),
                info.get("numero_historia"),
            ),
        )
        self.conn.commit()

    def get(self) -> Optional[Dict[str, Any]]:
        cur = self.conn.cursor()
        row = cur.execute("SELECT * FROM paciente LIMIT 1").fetchone()
        return dict(row) if row else None
