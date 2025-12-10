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

    def ensure(self, d: Dict[str, Any]) -> int:
        analisis_id = d.get("analisis_id")
        if analisis_id is not None:
            return int(analisis_id)

        fecha = d.get("fecha_analisis")
        numero_peticion = d.get("numero_peticion")
        origen = d.get("origen")

        if not fecha:
            raise ValueError("No se ha proporcionado analisis_id ni fecha_analisis.")

        return self.create(
            {
                "fecha_analisis": fecha,
                "numero_peticion": numero_peticion,
                "origen": origen,
            }
        )

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
