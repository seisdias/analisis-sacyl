# -*- coding: utf-8 -*-
"""
Gestor de base de datos para análisis de hematología + bioquímica + gasometría + orina.
Autor: Borja Alonso Tristán
Actualizado para soportar múltiples series de laboratorio.
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional


class HematologyDB:
    """
    Base de datos SQLite que contiene:

      - paciente
      - hematologia
      - bioquimica
      - gasometria
      - orina

    Y funciones de lectura/escritura para cada serie.
    """

    # ===== Campos de hematología en orden fijo =====
    DB_FIELDS_ORDER = [
        "id",
        "fecha_extraccion",
        "numero_peticion",
        "origen",
        "leucocitos",
        "neutrofilos_pct",
        "linfocitos_pct",
        "monocitos_pct",
        "eosinofilos_pct",
        "basofilos_pct",
        "neutrofilos_abs",
        "linfocitos_abs",
        "monocitos_abs",
        "eosinofilos_abs",
        "basofilos_abs",
        "hematies",
        "hemoglobina",
        "hematocrito",
        "vcm",
        "hcm",
        "chcm",
        "rdw",
        "plaquetas",
        "vpm"
    ]

    def __init__(self):
        self.conn: Optional[sqlite3.Connection] = None
        self.is_open: bool = False
        self.path: Optional[str] = None

    # ======================================================
    #   GESTIÓN DE ARCHIVO BD
    # ======================================================
    def create_new(self, path: str, overwrite: bool = False) -> None:
        if overwrite and Path(path).exists():
            Path(path).unlink()

        self.conn = sqlite3.connect(path)
        self.is_open = True
        self.path = path

        self._create_schema()

    def open_existing(self, path: str) -> None:
        if not Path(path).exists():
            raise FileNotFoundError(f"La base de datos '{path}' no existe.")

        self.conn = sqlite3.connect(path)
        self.is_open = True
        self.path = path

        self._create_schema()  # asegura que estén las tablas nuevas

    def close(self) -> None:
        if self.conn:
            self.conn.close()
        self.conn = None
        self.is_open = False
        self.path = None

    # ======================================================
    #   CREACIÓN DE TABLAS
    # ======================================================
    def _create_schema(self):
        """
        Crea (si no existen) todas las tablas necesarias.
        """
        c = self.conn.cursor()

        # ---- Paciente ----
        c.execute("""
            CREATE TABLE IF NOT EXISTS paciente (
                id INTEGER PRIMARY KEY,
                nombre TEXT,
                apellidos TEXT,
                fecha_nacimiento TEXT,
                sexo TEXT,
                numero_historia TEXT
            )
        """)

        # ---- Hematología ----
        c.execute("""
            CREATE TABLE IF NOT EXISTS hematologia (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha_extraccion TEXT,
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

        # ---- Bioquímica ----
        c.execute("""
        CREATE TABLE IF NOT EXISTS bioquimica (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_extraccion TEXT,
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

        # ---- Gasometría ----
        c.execute("""
        CREATE TABLE IF NOT EXISTS gasometria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_extraccion TEXT,
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

        # ---- Orina ----
        c.execute("""
        CREATE TABLE IF NOT EXISTS orina (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_extraccion TEXT,
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

    # ======================================================
    #   PACIENTE
    # ======================================================
    def get_patient(self):
        c = self.conn.cursor()
        r = c.execute("SELECT nombre, apellidos, fecha_nacimiento, sexo, numero_historia FROM paciente LIMIT 1").fetchone()
        if not r:
            return None
        return {
            "nombre": r[0],
            "apellidos": r[1],
            "fecha_nacimiento": r[2],
            "sexo": r[3],
            "numero_historia": r[4],
        }

    def check_and_update_patient(self, pac: Dict[str, Any]) -> None:
        """
        Inserta o valida paciente.
        Si ya existe, verifica match y actualiza Nº historia si antes era None.
        """
        c = self.conn.cursor()
        r = c.execute("SELECT id, nombre, apellidos, fecha_nacimiento, sexo, numero_historia FROM paciente").fetchone()

        if not r:
            # No existe aún → insert
            c.execute("""
                INSERT INTO paciente(nombre,apellidos,fecha_nacimiento,sexo,numero_historia)
                VALUES (?,?,?,?,?)
            """, (
                pac.get("nombre"), pac.get("apellidos"), pac.get("fecha_nacimiento"),
                pac.get("sexo"), pac.get("numero_historia")
            ))
            self.conn.commit()
            return

        # Ya existe: comprobar coincidencia salvo abreviaciones
        _, n, a, f, s, nh = r

        if pac.get("nombre") and n and not self._match_names(n, pac.get("nombre")):
            raise ValueError("Los datos de NOMBRE del paciente no coinciden.")

        if pac.get("apellidos") and a and a.strip().lower() != pac["apellidos"].strip().lower():
            raise ValueError("Los APELLIDOS no coinciden.")

        if pac.get("fecha_nacimiento") and f and f != pac["fecha_nacimiento"]:
            raise ValueError("La FECHA DE NACIMIENTO no coincide.")

        if pac.get("sexo") and s and s != pac["sexo"]:
            raise ValueError("El SEXO no coincide.")

        # Actualizar historia si estaba vacía
        if nh in (None, "", " ") and pac.get("numero_historia"):
            c.execute("UPDATE paciente SET numero_historia=? WHERE id=?", (pac["numero_historia"], r[0]))
            self.conn.commit()

    def _match_names(self, a: str, b: str) -> bool:
        """
        Acepta equivalencias tipo "L Borja" == "Luis Borja".
        """
        a = a.lower().strip()
        b = b.lower().strip()

        # Si uno es abreviado y coincide apellido/nombre final:
        if a.startswith(b[0]) or b.startswith(a[0]):
            return True
        return a == b

    # ======================================================
    #   IMPORTACIÓN JSON (TODAS LAS SERIES)
    # ======================================================
    def import_from_json(self, data: Dict[str, Any]) -> List[int]:
        """
        Inserta hematología + bioquímica + gasometría + orina.
        Devuelve lista de IDs insertados (hematología).
        """
        ids = []
        c = self.conn.cursor()

        # --------------------------------------------------
        # Hematología
        # --------------------------------------------------
        for h in data.get("hematologia", []) or data.get("analisis", []):
            fields = [
                "fecha_analisis", "numero_peticion", "origen",
                "leucocitos", "neutrofilos_pct", "linfocitos_pct",
                "monocitos_pct", "eosinofilos_pct", "basofilos_pct",
                "neutrofilos_abs", "linfocitos_abs", "monocitos_abs",
                "eosinofilos_abs", "basofilos_abs", "hematies",
                "hemoglobina", "hematocrito", "vcm", "hcm",
                "chcm", "rdw", "plaquetas", "vpm"
            ]
            vals = [h.get(f) for f in fields]
            c.execute(f"""
                INSERT INTO hematologia(
                    fecha_extraccion, numero_peticion, origen,
                    leucocitos, neutrofilos_pct, linfocitos_pct,
                    monocitos_pct, eosinofilos_pct, basofilos_pct,
                    neutrofilos_abs, linfocitos_abs, monocitos_abs,
                    eosinofilos_abs, basofilos_abs, hematies,
                    hemoglobina, hematocrito, vcm, hcm,
                    chcm, rdw, plaquetas, vpm
                ) VALUES ({",".join(["?"]*len(vals))})
            """, vals)
            ids.append(c.lastrowid)

        # --------------------------------------------------
        # Bioquímica
        # --------------------------------------------------
        for b in data.get("bioquimica", []):
            fields = [
                "fecha_analisis", "numero_peticion", "glucosa", "urea", "creatinina",
                "sodio", "potasio", "cloro", "calcio", "fosforo",
                "colesterol_total", "colesterol_hdl", "colesterol_ldl",
                "colesterol_no_hdl", "trigliceridos",
                "indice_riesgo", "hierro", "ferritina", "vitamina_b12"
            ]
            vals = [b.get(f) for f in fields]
            c.execute(f"""
                INSERT INTO bioquimica(
                    fecha_extraccion, numero_peticion, glucosa, urea, creatinina,
                    sodio, potasio, cloro, calcio, fosforo,
                    colesterol_total, colesterol_hdl, colesterol_ldl,
                    colesterol_no_hdl, trigliceridos, indice_riesgo,
                    hierro, ferritina, vitamina_b12
                ) VALUES ({",".join(["?"]*len(vals))})
            """, vals)

        # --------------------------------------------------
        # Gasometría
        # --------------------------------------------------
        for g in data.get("gasometria", []):
            fields = [
                "fecha_analisis", "numero_peticion", "gaso_ph", "gaso_pco2", "gaso_po2",
                "gaso_tco2", "gaso_so2_calc", "gaso_so2", "gaso_p50", "gaso_bicarbonato",
                "gaso_sbc", "gaso_eb", "gaso_beecf", "gaso_lactato"
            ]
            vals = [g.get(f) for f in fields]
            c.execute(f"""
                INSERT INTO gasometria(
                    fecha_extraccion, numero_peticion, gaso_ph, gaso_pco2, gaso_po2,
                    gaso_tco2, gaso_so2_calc, gaso_so2, gaso_p50, gaso_bicarbonato,
                    gaso_sbc, gaso_eb, gaso_beecf, gaso_lactato
                ) VALUES ({",".join(["?"]*len(vals))})
            """, vals)

        # --------------------------------------------------
        # Orina
        # --------------------------------------------------
        for o in data.get("orina", []):
            fields = [
                "fecha_analisis", "numero_peticion", "ph", "densidad", "glucosa",
                "proteinas", "cuerpos_cetonicos", "sangre", "nitritos",
                "leucocitos_ests", "bilirrubina", "urobilinogeno",
                "sodio_ur", "creatinina_ur", "indice_albumina_creatinina",
                "albumina_ur", "categoria_albuminuria"
            ]
            vals = [o.get(f) for f in fields]
            c.execute(f"""
                INSERT INTO orina(
                    fecha_extraccion, numero_peticion, ph, densidad, glucosa,
                    proteinas, cuerpos_cetonicos, sangre, nitritos,
                    leucocitos_ests, bilirrubina, urobilinogeno,
                    sodio_ur, creatinina_ur, indice_albumina_creatinina,
                    albumina_ur, categoria_albuminuria
                ) VALUES ({",".join(["?"]*len(vals))})
            """, vals)

        self.conn.commit()
        return ids

    # ======================================================
    #   CONSULTA PRINCIPAL (solo hematología por ahora)
    # ======================================================
    def list_analyses(self, limit=1000) -> List[tuple]:
        return self.conn.execute(
            f"SELECT {','.join(self.DB_FIELDS_ORDER)} "
            "FROM hematologia ORDER BY fecha_extraccion ASC LIMIT ?",
            (limit,)
        ).fetchall()