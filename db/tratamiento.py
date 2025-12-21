# db/tratamiento.py
# -*- coding: utf-8 -*-

import sqlite3
from typing import Dict, List, Any


class Tratamiento:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    # --------------------
    #   TREATMENT COURSE
    # --------------------
    def list_treatments(self) -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        rows = cur.execute("SELECT * FROM treatment_course ORDER BY start_date").fetchall()
        return [dict(r) for r in rows]

    def create_treatment(self, d: Dict[str, Any]) -> int:
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO treatment_course(name,start_date,end_date,standard_days,notes) "
            "VALUES(?,?,?,?,?)",
            (
                d.get("name"),
                d.get("start_date"),
                d.get("end_date"),
                d.get("standard_days"),
                d.get("notes"),
            ),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def update_treatment(self, treatment_id: int, d: Dict[str, Any]) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE treatment_course SET name=?, start_date=?, end_date=?, standard_days=?, notes=? WHERE id=?",
            (
                d.get("name"),
                d.get("start_date"),
                d.get("end_date"),
                d.get("standard_days"),
                d.get("notes"),
                treatment_id,
            ),
        )
        self.conn.commit()

    def delete_treatment(self, treatment_id: int) -> None:
        cur = self.conn.cursor()
        cur.execute("DELETE FROM treatment_course WHERE id=?", (treatment_id,))
        self.conn.commit()



