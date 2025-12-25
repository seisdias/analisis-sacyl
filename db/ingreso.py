# db/ingreso.py
# -*- coding: utf-8 -*-

import sqlite3
from typing import List, Dict, Any


class Ingreso:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    # --------------------
    #   HOSPITAL STAYS
    # --------------------
    def list_hospital_stays(self) -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        rows = cur.execute("SELECT * FROM hospital_stay ORDER BY admission_date").fetchall()
        return [dict(r) for r in rows]

    def create_hospital_stay(self, d: Dict[str, Any]) -> int:
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO hospital_stay(admission_date,discharge_date,notes) VALUES(?,?,?)",
            (d.get("admission_date"), d.get("discharge_date"), d.get("notes")),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def update_hospital_stay(self, stay_id: int, d: Dict[str, Any]) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE hospital_stay SET admission_date=?, discharge_date=?, notes=? WHERE id=?",
            (d.get("admission_date"), d.get("discharge_date"), d.get("notes"), stay_id),
        )
        self.conn.commit()

    def delete_hospital_stay(self, stay_id: int) -> None:
        cur = self.conn.cursor()
        cur.execute("DELETE FROM hospital_stay WHERE id=?", (stay_id,))
        self.conn.commit()


