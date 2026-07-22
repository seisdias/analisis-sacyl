# db/hematologia.py
# -*- coding: utf-8 -*-

import sqlite3
from typing import Dict, Any, List, Optional, Tuple

from .analisis import Analisis


class Hematologia:
    def __init__(self, conn: sqlite3.Connection, analisis: Analisis):
        self.conn = conn
        self.analisis = analisis

    def insert(self, d: Dict[str, Any], commit: bool = True) -> None:
        analisis_id = self.analisis.ensure(d, commit=commit)

        fields = [
            "analisis_id",
            "leucocitos", "neutrofilos_pct", "linfocitos_pct", "monocitos_pct",
            "eosinofilos_pct", "basofilos_pct",
            "neutrofilos_abs", "linfocitos_abs", "monocitos_abs",
            "eosinofilos_abs", "basofilos_abs",
            "hematies", "hemoglobina", "hematocrito", "vcm", "hcm", "chcm", "rdw",
            "plaquetas", "vpm",
        ]
        values = [analisis_id] + [d.get(f) for f in fields[1:]]
        cur = self.conn.cursor()

        # --- UPSERT por analisis_id ---
        update_cols = [f for f in fields if f != "analisis_id"]
        set_clause = ", ".join([f"{c}=excluded.{c}" for c in update_cols])

        cur.execute(
            f"""
            INSERT INTO hematologia ({",".join(fields)})
            VALUES ({",".join(["?"] * len(fields))})
            ON CONFLICT(analisis_id) DO UPDATE SET
                {set_clause}
            """,
            values,
        )

        if commit:
            self.conn.commit()

    def list(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        sql = """
            SELECT hematologia.*,
                   analisis.fecha_analisis,
                   analisis.numero_peticion,
                   analisis.origen
            FROM hematologia
            JOIN analisis ON hematologia.analisis_id = analisis.id
            ORDER BY analisis.fecha_analisis ASC
        """
        params: Tuple[Any, ...] = ()
        if limit is not None:
            sql += " LIMIT ?"
            params = (limit,)

        rows = cur.execute(sql, params).fetchall()
        aux = [dict(r) for r in rows]
        return aux

    def list_distinct_dates(self) -> List[str]:
        """
        Devuelve la lista de fechas (ISO YYYY-MM-DD) para las que existe
        al menos una analítica de hematología.
        Ordenadas de más reciente a más antigua.
        """
        cur = self.conn.cursor()

        rows = cur.execute(
            """
            SELECT DISTINCT analisis.fecha_analisis
            FROM hematologia
            JOIN analisis ON hematologia.analisis_id = analisis.id
            WHERE analisis.fecha_analisis IS NOT NULL
            ORDER BY analisis.fecha_analisis DESC
            """
        ).fetchall()

        # row_factory = sqlite3.Row → acceso por nombre
        return [r["fecha_analisis"] for r in rows]


    def get_by_fecha(self, fecha_analisis: str) -> Optional[Dict[str, Any]]:
        """
        Devuelve la fila de hematología correspondiente a una fecha concreta.
        Si hay varios análisis el mismo día, devuelve el más reciente (mayor analisis.id).
        """
        cur = self.conn.cursor()
        row = cur.execute(
            """
            SELECT h.*
            FROM hematologia h
            JOIN analisis a ON h.analisis_id = a.id
            WHERE a.fecha_analisis = ?
            ORDER BY a.id DESC
            LIMIT 1
            """,
            (fecha_analisis,),
        ).fetchone()

        return dict(row) if row else None

