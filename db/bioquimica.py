# db/bioquimica.py
# -*- coding: utf-8 -*-

import sqlite3
from typing import Dict, Any, List, Optional, Tuple

from .analisis import Analisis


class Bioquimica:
    def __init__(self, conn: sqlite3.Connection, analisis: Analisis):
        self.conn = conn
        self.analisis = analisis

    def insert(self, d: Dict[str, Any]) -> None:
        analisis_id = self.analisis.ensure(d)

        fields = [
            "analisis_id",
            "glucosa", "urea", "creatinina",
            "sodio", "potasio", "cloro", "calcio", "fosforo",
            "colesterol_total", "colesterol_hdl", "colesterol_ldl",
            "colesterol_no_hdl", "trigliceridos", "indice_riesgo",
            "hierro", "ferritina", "vitamina_b12",
        ]
        values = [analisis_id] + [d.get(f) for f in fields[1:]]

        cur = self.conn.cursor()
        cur.execute(
            f"INSERT INTO bioquimica ({','.join(fields)}) VALUES ({','.join(['?']*len(fields))})",
            values,
        )
        self.conn.commit()

    def list(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        sql = """
            SELECT bioquimica.*,
                   analisis.fecha_analisis,
                   analisis.numero_peticion,
                   analisis.origen
            FROM bioquimica
            JOIN analisis ON bioquimica.analisis_id = analisis.id
            ORDER BY analisis.fecha_analisis ASC
        """
        params: Tuple[Any, ...] = ()
        if limit is not None:
            sql += " LIMIT ?"
            params = (limit,)

        rows = cur.execute(sql, params).fetchall()
        aux = [dict(r) for r in rows]
        return aux
