# db/limite_parametro.py
# -*- coding: utf-8 -*-

import sqlite3
from typing import Optional, List, Dict, Any


class LimiteParametro:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    # --------------------
    #   PARAM LIMITS
    # --------------------
    def list_param_limits(self, param_key: Optional[str] = None) -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        if param_key:
            rows = cur.execute(
                "SELECT * FROM param_limit WHERE param_key=? ORDER BY value",
                (param_key,),
            ).fetchall()
        else:
            rows = cur.execute("SELECT * FROM param_limit ORDER BY param_key, value").fetchall()
        return [dict(r) for r in rows]

    def create_param_limit(self, d: Dict[str, Any]) -> int:
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO param_limit(param_key,value,label,enabled) VALUES(?,?,?,?)",
            (d["param_key"], d["value"], d.get("label"), int(d.get("enabled", 1))),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def update_param_limit(self, limit_id: int, d: Dict[str, Any]) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE param_limit SET param_key=?, value=?, label=?, enabled=? WHERE id=?",
            (d["param_key"], d["value"], d.get("label"), int(d.get("enabled", 1)), limit_id),
        )
        self.conn.commit()

    def delete_param_limit(self, limit_id: int) -> None:
        cur = self.conn.cursor()
        cur.execute("DELETE FROM param_limit WHERE id=?", (limit_id,))
        self.conn.commit()


