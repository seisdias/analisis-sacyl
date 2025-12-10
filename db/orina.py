# db/orina.py
# -*- coding: utf-8 -*-

import sqlite3
from typing import Dict, Any, List, Optional, Tuple

from .analisis import Analisis


class Orina:
    def __init__(self, conn: sqlite3.Connection, analisis: Analisis):
        self.conn = conn
        self.analisis = analisis

    def insert(self, d: Dict[str, Any]) -> None:
        analisis_id = self.analisis.ensure(d)

        fields = [
            "analisis_id",
            "ph", "densidad",
            "glucosa", "proteinas", "cuerpos_cetonicos", "sangre",
            "nitritos", "leucocitos_ests", "bilirrubina", "urobilinogeno",
            "sodio_ur", "creatinina_ur",
            "indice_albumina_creatinina", "albumina_ur",
            "categoria_albuminuria",
        ]
        values = [analisis_id] + [d.get(f) for f in fields[1:]]

        cur = self.conn.cursor()
        cur.execute(
            f"INSERT INTO orina ({','.join(fields)}) VALUES ({','.join(['?']*len(fields))})",
            values,
        )
        self.conn.commit()

    def list(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        sql = """
            SELECT orina.*,
                   analisis.fecha_analisis,
                   analisis.numero_peticion,
                   analisis.origen
            FROM orina
            JOIN analisis ON orina.analisis_id = analisis.id
            ORDER BY analisis.fecha_analisis ASC
        """
        params: Tuple[Any, ...] = ()
        if limit is not None:
            sql += " LIMIT ?"
            params = (limit,)

        rows = cur.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
