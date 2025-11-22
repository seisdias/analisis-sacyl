# -*- coding: utf-8 -*-
"""
Módulo de gestión de base de datos para análisis de hematología.
Autor: Borja Alonso Tristán
Año: 2025
"""

import sqlite3
import json
import unicodedata
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple, Union


# Esquema básico de la tabla de hematología + tabla de paciente.
DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS hematologia (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    -- Metadatos del análisis
    fecha_extraccion TEXT NOT NULL,         -- ISO: 'YYYY-MM-DD'
    numero_peticion TEXT,
    origen TEXT,

    -- SERIE BLANCA
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

    -- SERIE ROJA
    hematies REAL,
    hemoglobina REAL,
    hematocrito REAL,
    vcm REAL,
    hcm REAL,
    chcm REAL,
    rdw REAL,

    -- SERIE PLAQUETAR
    plaquetas REAL,
    vpm REAL
);

CREATE TABLE IF NOT EXISTS paciente (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT,
    apellidos TEXT,
    fecha_nacimiento TEXT,
    sexo TEXT,
    numero_historia TEXT
);
"""


class HematologyDB:
    """
    Clase para gestionar una BD SQLite de análisis de hematología.
    """

    # Orden de columnas tal y como las devuelve list_analyses() / get_analysis_by_id()
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
        "vpm",
    ]

    def __init__(self) -> None:
        self._conn: Optional[sqlite3.Connection] = None
        self._db_path: Optional[Path] = None

    # --------------------------------------------------
    #  Apertura / creación / cierre
    # --------------------------------------------------
    def create_new(self, path: str, overwrite: bool = False) -> None:
        """
        Crea una NUEVA base de datos en 'path'.

        - Si ya existe y overwrite=False -> lanza FileExistsError.
        - Si ya existe y overwrite=True  -> borra el archivo y crea una nueva.
        """
        db_path = Path(path)

        if db_path.exists():
            if not overwrite:
                raise FileExistsError(
                    f"La base de datos '{db_path}' ya existe. "
                    f"Usa overwrite=True si quieres reemplazarla."
                )
            db_path.unlink()  # eliminamos la BD existente

        # Cerramos cualquier conexión previa
        self.close()

        self._conn = sqlite3.connect(db_path)
        self._db_path = db_path
        self._create_schema()

    def open_existing(self, path: str) -> None:
        """
        Abre una base de datos EXISTENTE en 'path'.
        Lanza FileNotFoundError si el archivo no existe.
        """
        db_path = Path(path)

        if not db_path.exists():
            raise FileNotFoundError(
                f"La base de datos '{db_path}' no existe. "
                f"Si quieres crear una nueva, usa create_new()."
            )

        # Cerramos cualquier conexión previa
        self.close()

        self._conn = sqlite3.connect(db_path)
        self._db_path = db_path
        # Por si la BD es antigua o estaba vacía, aseguramos el esquema (hematologia + paciente)
        self._create_schema()

    def open(self, path: str) -> None:
        """
        Atajo: si existe, la abre. Si no existe, la crea.
        """
        db_path = Path(path)
        if db_path.exists():
            self.open_existing(path)
        else:
            self.create_new(path, overwrite=False)

    def _create_schema(self) -> None:
        """
        Crea las tablas necesarias si no existen (hematologia, paciente).
        """
        if self._conn is None:
            raise RuntimeError("Base de datos no abierta.")
        with self._conn:
            self._conn.executescript(DB_SCHEMA)

    def close(self) -> None:
        """
        Cierra la conexión abierta, si la hay.
        """
        if self._conn is not None:
            self._conn.close()
            self._conn = None
            self._db_path = None

    @property
    def is_open(self) -> bool:
        """Devuelve True si hay una BD abierta."""
        return self._conn is not None

    @property
    def path(self) -> Optional[str]:
        """Ruta actual de la BD abierta (o None si no hay)."""
        return str(self._db_path) if self._db_path is not None else None

    # --------------------------------------------------
    #  Gestión de datos de paciente
    # --------------------------------------------------
    def get_patient(self) -> Optional[Dict[str, Any]]:
        """
        Devuelve los datos del paciente (primer registro de la tabla 'paciente'),
        o None si no hay ninguno.
        """
        if self._conn is None:
            raise RuntimeError("No hay base de datos abierta.")

        cur = self._conn.execute(
            """
            SELECT id, nombre, apellidos, fecha_nacimiento, sexo, numero_historia
            FROM paciente
            ORDER BY id ASC
            LIMIT 1
            """
        )
        row = cur.fetchone()
        if row is None:
            return None

        return {
            "id": row[0],
            "nombre": row[1],
            "apellidos": row[2],
            "fecha_nacimiento": row[3],
            "sexo": row[4],
            "numero_historia": row[5],
        }

    def _normalize_str(self, value: Any) -> str:
        """
        Normaliza cadenas para compararlas:
        - None -> ""
        - strip + upper
        - colapsa espacios múltiples en uno
        - elimina tildes (TRISTÁN -> TRISTAN)
        """
        if value is None:
            return ""
        s = str(value).strip().upper()
        # colapsar espacios múltiples
        s = " ".join(s.split())
        # quitar tildes
        s = unicodedata.normalize("NFD", s)
        s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
        return s



    def check_and_update_patient(self, paciente: Dict[str, Any]) -> None:
        """
        Verifica que los datos de paciente del JSON coinciden con los
        ya almacenados en la BD y, si no hay registro, lo crea.

        Reglas:
        - Si no existe paciente en la BD -> se inserta.
        - Campos estrictos: apellidos, fecha_nacimiento, sexo.
          * Si ambos lados tienen valor y difieren (tras normalizar) -> ValueError.
        - Nombre NO provoca error:
          * Si es compatible (abreviatura vs nombre completo) podemos actualizar.
          * Si no lo es, simplemente lo ignoramos (no lo tratamos como conflicto).
        - nº Historia: solo se rellena si antes estaba vacío y ahora viene informado.
        """
        if self._conn is None:
            raise RuntimeError("No hay base de datos abierta.")
        if not paciente:
            return

        existing = self.get_patient()

        def is_name_compatible(old_name: str, new_name: str) -> bool:
            """
            Devuelve True si podemos considerar que old_name y new_name
            son la misma persona con variación de abreviatura:
            - si uno es prefijo (normalizado) del otro
            - o comparten inicial y uno está contenido en el otro
            """
            if not old_name or not new_name:
                return True  # no lo tratamos como conflicto

            o = self._normalize_str(old_name)
            n = self._normalize_str(new_name)

            if not o or not n:
                return True

            # misma inicial
            if o[0] == n[0]:
                # ¿uno contiene/prefija al otro?
                if o in n or n in o:
                    return True

            return False

        # Datos nuevos normalizados
        nombre_new_norm = self._normalize_str(paciente.get("nombre"))
        apellidos_new_norm = self._normalize_str(paciente.get("apellidos"))
        fecha_new_norm = self._normalize_str(paciente.get("fecha_nacimiento"))
        sexo_new_norm = self._normalize_str(paciente.get("sexo"))
        nhist_new_norm = self._normalize_str(
            paciente.get("numero_historia") or paciente.get("n_historia")
        )

        if existing is None:
            # Insertamos primer paciente tal cual viene
            with self._conn:
                self._conn.execute(
                    """
                    INSERT INTO paciente (nombre, apellidos, fecha_nacimiento, sexo, numero_historia)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        paciente.get("nombre"),
                        paciente.get("apellidos"),
                        paciente.get("fecha_nacimiento"),
                        paciente.get("sexo"),
                        paciente.get("numero_historia") or paciente.get("n_historia"),
                    ),
                )
            return

        # --- Comprobamos discrepancias en campos estrictos ---
        mismatches = []

        # apellidos
        old_apellidos_norm = self._normalize_str(existing.get("apellidos"))
        if old_apellidos_norm and apellidos_new_norm and old_apellidos_norm != apellidos_new_norm:
            mismatches.append("apellidos")

        # fecha_nacimiento
        old_fecha_norm = self._normalize_str(existing.get("fecha_nacimiento"))
        if old_fecha_norm and fecha_new_norm and old_fecha_norm != fecha_new_norm:
            mismatches.append("fecha_nacimiento")

        # sexo
        old_sexo_norm = self._normalize_str(existing.get("sexo"))
        if old_sexo_norm and sexo_new_norm and old_sexo_norm != sexo_new_norm:
            mismatches.append("sexo")

        # --- Nombre: nunca dispara error, solo se usa para mejorar dato ---
        # Si quisieras, podrías loguear incompatibilidades, pero NO añadir a mismatches.
        old_name_raw = existing.get("nombre")
        old_name_norm = self._normalize_str(old_name_raw)

        if mismatches:
            raise ValueError(
                "Los datos del paciente del informe no coinciden con la base de datos actual "
                f"(campos en conflicto: {', '.join(mismatches)})."
            )

        # --- Actualizamos datos que antes estaban vacíos o abreviados ---
        updates = {}

        # Nombre: si nuevo es “mejor” (más largo y compatible) o antes no había nada
        if nombre_new_norm:
            if not old_name_norm:
                updates["nombre"] = paciente.get("nombre")
            else:
                if is_name_compatible(old_name_raw or "", paciente.get("nombre") or "") \
                        and len(nombre_new_norm) > len(old_name_norm):
                    updates["nombre"] = paciente.get("nombre")

        # Apellidos, fecha de nacimiento, sexo, nº historia: solo si estaban vacíos
        for field in ["apellidos", "fecha_nacimiento", "sexo", "numero_historia"]:
            old_norm = self._normalize_str(existing.get(field))
            new_raw = paciente.get(field) or ""
            if not old_norm and str(new_raw).strip():
                updates[field] = new_raw

        if updates:
            set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
            params = list(updates.values())
            params.append(existing["id"])
            with self._conn:
                self._conn.execute(
                    f"UPDATE paciente SET {set_clause} WHERE id = ?", params
                )



    # --------------------------------------------------
    #  Operaciones sobre la tabla hematologia
    # --------------------------------------------------
    def insert_hematology_row(self, data: Dict[str, Any]) -> int:
        """
        Inserta un análisis de hematología en la tabla.

        'data' debe contener como mínimo 'fecha_extraccion' (ISO 'YYYY-MM-DD').

        Claves admitidas:
        fecha_extraccion, numero_peticion, origen,
        leucocitos, neutrofilos_pct, linfocitos_pct,
        monocitos_pct, eosinofilos_pct, basofilos_pct,
        neutrofilos_abs, linfocitos_abs, monocitos_abs,
        eosinofilos_abs, basofilos_abs,
        hematies, hemoglobina, hematocrito, vcm,
        hcm, chcm, rdw,
        plaquetas, vpm.
        """
        if self._conn is None:
            raise RuntimeError("No hay base de datos abierta.")

        if "fecha_extraccion" not in data or not data["fecha_extraccion"]:
            raise ValueError("El campo 'fecha_extraccion' es obligatorio.")

        columns = [
            "fecha_extraccion", "numero_peticion", "origen",
            "leucocitos", "neutrofilos_pct", "linfocitos_pct",
            "monocitos_pct", "eosinofilos_pct", "basofilos_pct",
            "neutrofilos_abs", "linfocitos_abs", "monocitos_abs",
            "eosinofilos_abs", "basofilos_abs",
            "hematies", "hemoglobina", "hematocrito", "vcm",
            "hcm", "chcm", "rdw",
            "plaquetas", "vpm"
        ]

        values = [data.get(col) for col in columns]

        placeholders = ", ".join(["?"] * len(columns))
        col_names = ", ".join(columns)

        sql = f"INSERT INTO hematologia ({col_names}) VALUES ({placeholders})"

        with self._conn:
            cur = self._conn.execute(sql, values)
            return int(cur.lastrowid)

    def upsert_hematology_row(self, data: Dict[str, Any]) -> int:
        """
        Inserta o reemplaza un análisis según la fecha de extracción.

        - Si NO hay registro con esa fecha_extraccion -> INSERT.
        - Si SÍ hay registro con esa fecha_extraccion -> UPDATE (se reemplaza).

        Devuelve el ID del registro afectado.
        """
        if self._conn is None:
            raise RuntimeError("No hay base de datos abierta.")

        # Aceptamos también 'fecha_analisis' y la mapeamos
        if "fecha_extraccion" not in data or not data["fecha_extraccion"]:
            if "fecha_analisis" in data and data["fecha_analisis"]:
                data["fecha_extraccion"] = data["fecha_analisis"]
            else:
                raise ValueError(
                    "Es obligatorio un campo de fecha ('fecha_extraccion' "
                    "o 'fecha_analisis')."
                )

        fecha = data["fecha_extraccion"]

        # ¿Ya hay un análisis para esa fecha?
        cur = self._conn.execute(
            "SELECT id FROM hematologia WHERE fecha_extraccion = ?",
            (fecha,)
        )
        row = cur.fetchone()

        if row is None:
            # No existe -> insertamos
            return self.insert_hematology_row(data)

        # Sí existe -> hacemos UPDATE
        analysis_id = int(row[0])

        columns = [
            "numero_peticion", "origen",
            "leucocitos", "neutrofilos_pct", "linfocitos_pct",
            "monocitos_pct", "eosinofilos_pct", "basofilos_pct",
            "neutrofilos_abs", "linfocitos_abs", "monocitos_abs",
            "eosinofilos_abs", "basofilos_abs",
            "hematies", "hemoglobina", "hematocrito", "vcm",
            "hcm", "chcm", "rdw",
            "plaquetas", "vpm"
        ]

        # Construimos SET dinámico: col1 = ?, col2 = ?, ...
        set_clause = ", ".join(f"{col} = ?" for col in columns)
        values = [data.get(col) for col in columns]
        values.append(analysis_id)

        sql = f"UPDATE hematologia SET {set_clause} WHERE id = ?"

        with self._conn:
            self._conn.execute(sql, values)

        return analysis_id

    def list_analyses(self, limit: int = 100) -> List[Tuple[Any, ...]]:
        """
        Devuelve una lista de análisis (tuplas) ordenados por fecha ascendente.
        """
        if self._conn is None:
            raise RuntimeError("No hay base de datos abierta.")

        sql = """
            SELECT
                id, fecha_extraccion, numero_peticion, origen,
                leucocitos, neutrofilos_pct, linfocitos_pct, monocitos_pct,
                eosinofilos_pct, basofilos_pct,
                neutrofilos_abs, linfocitos_abs, monocitos_abs,
                eosinofilos_abs, basofilos_abs,
                hematies, hemoglobina, hematocrito, vcm,
                hcm, chcm, rdw,
                plaquetas, vpm
            FROM hematologia
            ORDER BY fecha_extraccion ASC, id ASC
            LIMIT ?
        """
        cur = self._conn.execute(sql, (limit,))
        return cur.fetchall()

    def get_analysis_by_id(self, analysis_id: int) -> Optional[Tuple[Any, ...]]:
        """
        Devuelve un análisis concreto por su ID, o None si no existe.
        """
        if self._conn is None:
            raise RuntimeError("No hay base de datos abierta.")

        sql = """
            SELECT
                id, fecha_extraccion, numero_peticion, origen,
                leucocitos, neutrofilos_pct, linfocitos_pct, monocitos_pct,
                eosinofilos_pct, basofilos_pct,
                neutrofilos_abs, linfocitos_abs, monocitos_abs,
                eosinofilos_abs, basofilos_abs,
                hematies, hemoglobina, hematocrito, vcm,
                hcm, chcm, rdw,
                plaquetas, vpm
            FROM hematologia
            WHERE id = ?
        """
        cur = self._conn.execute(sql, (analysis_id,))
        row = cur.fetchone()
        return row

    # --------------------------------------------------
    #  Importación desde JSON (serie completa)
    # --------------------------------------------------
    def import_from_json(
        self,
        json_data: Union[str, Dict[str, Any], List[Dict[str, Any]]]
    ) -> List[int]:
        """
        Inserta / reemplaza una serie de análisis procedente de un JSON.

        Ahora admite opcionalmente un bloque "paciente" con los datos:
        {
            "paciente": {...},
            "analisis": [ {...}, {...} ]
        }

        Política:
        - Si ya existe un análisis para una fecha, se REEMPLAZA (UPDATE).
        - Si no existe, se INSERTA.
        - Si los datos de paciente no coinciden con los ya almacenados,
          lanza ValueError.
        """
        if self._conn is None:
            raise RuntimeError("No hay base de datos abierta.")

        # 1) Parseo si viene como string
        if isinstance(json_data, str):
            payload = json.loads(json_data)
        else:
            payload = json_data

        paciente_dict: Optional[Dict[str, Any]] = None

        # 2) Normalizamos para obtener una lista de análisis
        if isinstance(payload, list):
            analyses_list = payload
        elif isinstance(payload, dict):
            # Datos de paciente (opcional)
            if isinstance(payload.get("paciente"), dict):
                paciente_dict = payload.get("paciente")

            if "analisis" in payload and isinstance(payload["analisis"], list):
                analyses_list = payload["analisis"]
            elif "analyses" in payload and isinstance(payload["analyses"], list):
                analyses_list = payload["analyses"]
            elif "data" in payload and isinstance(payload["data"], list):
                analyses_list = payload["data"]
            else:
                # Podría ser un único análisis en forma de dict
                analyses_list = [payload]
        else:
            raise TypeError("Formato de json_data no soportado para import_from_json.")

        # 3) Verificar / actualizar paciente
        if paciente_dict:
            self.check_and_update_patient(paciente_dict)

        # 4) Insertar / upsert de análisis
        ids: List[int] = []

        for item in analyses_list:
            if not isinstance(item, dict):
                continue  # ignoramos elementos raros

            analysis_id = self.upsert_hematology_row(item)
            ids.append(analysis_id)

        return ids
