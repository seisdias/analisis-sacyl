# db/gasometria.py
# -*- coding: utf-8 -*-

import sqlite3
from typing import Dict, Any, List, Optional, Tuple

from .analisis import Analisis


class Gasometria:
    def __init__(self, conn: sqlite3.Connection, analisis: Analisis):
        self.conn = conn
        self.analisis = analisis

    def insert(self, d: Dict[str, Any]) -> None:
        analisis_id = self.analisis.ensure(d)

        fields = [
            "analisis_id",
            "gaso_ph", "gaso_pco2", "gaso_po2", "gaso_tco2",
            "gaso_so2_calc", "gaso_so2", "gaso_p50",
            "gaso_bicarbonato", "gaso_sbc", "gaso_eb",
            "gaso_beecf", "gaso_lactato",
        ]
        values = [analisis_id] + [d.get(f) for f in fields[1:]]

        cur = self.conn.cursor()
        cur.execute(
            f"INSERT INTO gasometria ({','.join(fields)}) VALUES ({','.join(['?']*len(fields))})",
            values,
        )
        self.conn.commit()

    def list(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        sql = """
            SELECT gasometria.*,
                   analisis.fecha_analisis,
                   analisis.numero_peticion,
                   analisis.origen
            FROM gasometria
            JOIN analisis ON gasometria.analisis_id = analisis.id
            ORDER BY analisis.fecha_analisis ASC
        """
        params: Tuple[Any, ...] = ()
        if limit is not None:
            sql += " LIMIT ?"
            params = (limit,)

        rows = cur.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
