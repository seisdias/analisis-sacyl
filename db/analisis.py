# db/analisis.py
# -*- coding: utf-8 -*-

import sqlite3
from typing import Any, Dict, List, Optional, Tuple


class Analisis:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def create(self, info: Dict[str, Any]) -> int:
        fecha = info.get("fecha_analisis")
        if not fecha:
            raise ValueError("fecha_analisis es obligatorio para crear un analisis.")

        numero_peticion = info.get("numero_peticion")
        origen = info.get("origen")

        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO analisis (fecha_analisis, numero_peticion, origen)
            VALUES (?, ?, ?)
            """,
            (fecha, numero_peticion, origen),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def ensure(self, d: dict) -> int:
        analisis_id = d.get("analisis_id")
        if analisis_id:
            return int(analisis_id)

        fecha = d.get("fecha_analisis")
        num = d.get("numero_peticion")
        if not fecha or not num:
            raise ValueError("Se requiere 'fecha_analisis' y 'numero_peticion' si no se indica 'analisis_id'.")

        origen = d.get("origen")

        cur = self.conn.cursor()
        row = cur.execute(
            "SELECT id, origen FROM analisis WHERE fecha_analisis = ? AND numero_peticion = ?",
            (fecha, num),
        ).fetchone()

        if row:
            existing_id = int(row["id"])
            existing_origen = row["origen"]

            # “relleno tardío” del origen
            if origen and (existing_origen is None or str(existing_origen).strip() == ""):
                cur.execute(
                    "UPDATE analisis SET origen = ? WHERE id = ?",
                    (origen, existing_id),
                )
                self.conn.commit()

            return existing_id

        # Si no existe, crear (con origen si viene)
        cur.execute(
            "INSERT INTO analisis (fecha_analisis, numero_peticion, origen) VALUES (?, ?, ?)",
            (fecha, num, origen),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def list(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        sql = """
            SELECT *
            FROM analisis
            ORDER BY fecha_analisis ASC
        """
        params: Tuple[Any, ...] = ()
        if limit is not None:
            sql += " LIMIT ?"
            params = (limit,)

        rows = cur.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
