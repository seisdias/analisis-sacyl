# -*- coding: utf-8 -*-
"""
Gestor de base de datos local para análisis de laboratorio.
Compatible con:
 - Hematología (hemograma)
 - Bioquímica
 - Gasometría
 - Orina

Autor: Borja Alonso Tristán
Año: 2025
"""

import sqlite3
from typing import Dict, Any, List, Optional, Tuple


DB_FILE = "hematologia.db"


# ===============================================================
#   CLASE PRINCIPAL
# ===============================================================

class HematologyDB:
    """
    Gestor SQLite para almacenar análisis importados desde PDF.
    Estructura:
        paciente (1 fila)
        hematologia (N)
        bioquimica (N)
        gasometria (N)
        orina (N)
    """

    def __init__(self, db_path: str = DB_FILE):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self.is_open = False

    # ------------------------------------------------------------------
    #   APERTURA / CIERRE
    # ------------------------------------------------------------------

    def open(self):
        """Abre conexión y crea tablas si no existen."""
        if self.is_open:
            return

        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.is_open = True

        self._create_tables()

    def close(self):
        if self.conn and self.is_open:
            self.conn.close()
        self.is_open = False

    # ------------------------------------------------------------------
    #   CREACIÓN DE TABLAS
    # ------------------------------------------------------------------

    def _create_tables(self):
        cur = self.conn.cursor()

        # Tabla PACIENTE (solo una fila activa)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS paciente (
                id INTEGER PRIMARY KEY,
                nombre TEXT,
                apellidos TEXT,
                fecha_nacimiento TEXT,
                sexo TEXT,
                numero_historia TEXT
            )
        """)

        # ================== HEMATOLOGÍA ===================
        cur.execute("""
            CREATE TABLE IF NOT EXISTS hematologia (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha_analisis TEXT,
                numero_peticion TEXT,
                origen TEXT,
                leucocitos REAL,
                neutrofilos_pct REAL,
                linfocitos_pct REAL,
                monocitos_pct REAL,
                eosinofilos_pct REAL,
                basofilos_pct REAL,
                neutrofilos_abs REAL,
                linfocitos_abs REAL,
                monocitos_abs REAL,
                eosinofilos_abs REAL,
                basofilos_abs REAL,
                hematies REAL,
                hemoglobina REAL,
                hematocrito REAL,
                vcm REAL,
                hcm REAL,
                chcm REAL,
                rdw REAL,
                plaquetas REAL,
                vpm REAL
            )
        """)

        # ================== BIOQUÍMICA ===================
        cur.execute("""
            CREATE TABLE IF NOT EXISTS bioquimica (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha_analisis TEXT,
                numero_peticion TEXT,
                glucosa REAL,
                urea REAL,
                creatinina REAL,
                sodio REAL,
                potasio REAL,
                cloro REAL,
                calcio REAL,
                fosforo REAL,
                colesterol_total REAL,
                colesterol_hdl REAL,
                colesterol_ldl REAL,
                colesterol_no_hdl REAL,
                trigliceridos REAL,
                indice_riesgo REAL,
                hierro REAL,
                ferritina REAL,
                vitamina_b12 REAL
            )
        """)

        # ================== GASOMETRÍA ===================
        cur.execute("""
            CREATE TABLE IF NOT EXISTS gasometria (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha_analisis TEXT,
                numero_peticion TEXT,
                gaso_ph REAL,
                gaso_pco2 REAL,
                gaso_po2 REAL,
                gaso_tco2 REAL,
                gaso_so2_calc REAL,
                gaso_so2 REAL,
                gaso_p50 REAL,
                gaso_bicarbonato REAL,
                gaso_sbc REAL,
                gaso_eb REAL,
                gaso_beecf REAL,
                gaso_lactato REAL
            )
        """)

        # ================== ORINA ===================
        cur.execute("""
            CREATE TABLE IF NOT EXISTS orina (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha_analisis TEXT,
                numero_peticion TEXT,
                ph REAL,
                densidad REAL,
                glucosa TEXT,
                proteinas TEXT,
                cuerpos_cetonicos TEXT,
                sangre TEXT,
                nitritos TEXT,
                leucocitos_ests TEXT,
                bilirrubina TEXT,
                urobilinogeno TEXT,
                sodio_ur REAL,
                creatinina_ur REAL,
                indice_albumina_creatinina REAL,
                albumina_ur REAL,
                categoria_albuminuria TEXT
            )
        """)

        self.conn.commit()

    # ------------------------------------------------------------------
    #   GUARDAR DATOS DEL PACIENTE
    # ------------------------------------------------------------------

    def save_patient(self, info: Dict[str, Any]):
        """
        Guarda o actualiza los datos del paciente (solo 1 registro).
        """
        cur = self.conn.cursor()

        cur.execute("DELETE FROM paciente")

        cur.execute("""
            INSERT INTO paciente (nombre, apellidos, fecha_nacimiento, sexo, numero_historia)
            VALUES (?, ?, ?, ?, ?)
        """, (
            info.get("nombre"),
            info.get("apellidos"),
            info.get("fecha_nacimiento"),
            info.get("sexo"),
            info.get("numero_historia")
        ))

        self.conn.commit()

    def get_patient(self) -> Optional[Dict[str, Any]]:
        cur = self.conn.cursor()
        row = cur.execute("SELECT * FROM paciente LIMIT 1").fetchone()
        return dict(row) if row else None

    # ------------------------------------------------------------------
    #   INSERTAR SERIES
    # ------------------------------------------------------------------

    def insert_hematologia(self, d: Dict[str, Any]):
        cur = self.conn.cursor()

        fields = [
            "fecha_analisis", "numero_peticion", "origen",
            "leucocitos", "neutrofilos_pct", "linfocitos_pct", "monocitos_pct",
            "eosinofilos_pct", "basofilos_pct",
            "neutrofilos_abs", "linfocitos_abs", "monocitos_abs",
            "eosinofilos_abs", "basofilos_abs",
            "hematies", "hemoglobina", "hematocrito", "vcm", "hcm", "chcm", "rdw",
            "plaquetas", "vpm"
        ]

        values = [d.get(f) for f in fields]

        cur.execute(f"""
            INSERT INTO hematologia ({','.join(fields)})
            VALUES ({','.join(['?']*len(fields))})
        """, values)

        self.conn.commit()

    def insert_bioquimica(self, d: Dict[str, Any]):
        cur = self.conn.cursor()

        fields = [
            "fecha_analisis", "numero_peticion",
            "glucosa", "urea", "creatinina",
            "sodio", "potasio", "cloro", "calcio", "fosforo",
            "colesterol_total", "colesterol_hdl", "colesterol_ldl",
            "colesterol_no_hdl", "trigliceridos", "indice_riesgo",
            "hierro", "ferritina", "vitamina_b12"
        ]

        values = [d.get(f) for f in fields]

        cur.execute(f"""
            INSERT INTO bioquimica ({','.join(fields)})
            VALUES ({','.join(['?']*len(fields))})
        """, values)

        self.conn.commit()

    def insert_gasometria(self, d: Dict[str, Any]):
        cur = self.conn.cursor()

        fields = [
            "fecha_analisis", "numero_peticion",
            "gaso_ph", "gaso_pco2", "gaso_po2", "gaso_tco2",
            "gaso_so2_calc", "gaso_so2", "gaso_p50",
            "gaso_bicarbonato", "gaso_sbc", "gaso_eb",
            "gaso_beecf", "gaso_lactato"
        ]

        values = [d.get(f) for f in fields]

        cur.execute(f"""
            INSERT INTO gasometria ({','.join(fields)})
            VALUES ({','.join(['?']*len(fields))})
        """, values)

        self.conn.commit()

    def insert_orina(self, d: Dict[str, Any]):
        cur = self.conn.cursor()

        fields = [
            "fecha_analisis", "numero_peticion",
            "ph", "densidad",
            "glucosa", "proteinas", "cuerpos_cetonicos", "sangre",
            "nitritos", "leucocitos_ests", "bilirrubina", "urobilinogeno",
            "sodio_ur", "creatinina_ur",
            "indice_albumina_creatinina", "albumina_ur",
            "categoria_albuminuria"
        ]

        values = [d.get(f) for f in fields]

        cur.execute(f"""
            INSERT INTO orina ({','.join(fields)})
            VALUES ({','.join(['?']*len(fields))})
        """, values)

        self.conn.commit()

    # ------------------------------------------------------------------
    #   CONSULTAS PARA TABLAS Y GRÁFICAS
    # ------------------------------------------------------------------

    def list_hematologia(self) -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        rows = cur.execute("SELECT * FROM hematologia ORDER BY fecha_analisis ASC").fetchall()
        return [dict(r) for r in rows]

    def list_bioquimica(self) -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        rows = cur.execute("SELECT * FROM bioquimica ORDER BY fecha_analisis ASC").fetchall()
        return [dict(r) for r in rows]

    def list_gasometria(self) -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        rows = cur.execute("SELECT * FROM gasometria ORDER BY fecha_analisis ASC").fetchall()
        return [dict(r) for r in rows]

    def list_orina(self) -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        rows = cur.execute("SELECT * FROM orina ORDER BY fecha_analisis ASC").fetchall()
        return [dict(r) for r in rows]


# ===============================================================
#   FIN DEL MÓDULO
# ===============================================================