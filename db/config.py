# db/config.py
# -*- coding: utf-8 -*-

import sqlite3
from typing import Optional


class Config:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    # --------------------
    #   CONFIG
    # --------------------
    def config_get(self, key: str) -> Optional[str]:
        cur = self.conn.cursor()
        row = cur.execute("SELECT value FROM app_config WHERE key=?", (key,)).fetchone()
        return row["value"] if row else None

    def config_set(self, key: str, value: str) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO app_config(key,value) VALUES(?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
        self.conn.commit()

