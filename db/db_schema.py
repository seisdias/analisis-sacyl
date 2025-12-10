# db/db_schema.py
# -*- coding: utf-8 -*-

from typing import Any

SCHEMA_VERSION: int = 2

SCHEMA_SQL: str = """
-- ================== ANALISIS (DOCUMENTO) ===================
CREATE TABLE IF NOT EXISTS analisis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha_analisis TEXT NOT NULL,
    numero_peticion TEXT,
    origen TEXT
);

-- ================== PACIENTE ===================
CREATE TABLE IF NOT EXISTS paciente (
    id INTEGER PRIMARY KEY,
    nombre TEXT,
    apellidos TEXT,
    fecha_nacimiento TEXT,
    sexo TEXT,
    numero_historia TEXT
);

-- ================== HEMATOLOGÍA ===================
CREATE TABLE IF NOT EXISTS hematologia (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analisis_id INTEGER NOT NULL,
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
    vpm REAL,
    FOREIGN KEY (analisis_id) REFERENCES analisis(id) ON DELETE CASCADE
);

-- ================== BIOQUÍMICA ===================
CREATE TABLE IF NOT EXISTS bioquimica (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analisis_id INTEGER NOT NULL,
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
    vitamina_b12 REAL,
    FOREIGN KEY (analisis_id) REFERENCES analisis(id) ON DELETE CASCADE
);

-- ================== GASOMETRÍA ===================
CREATE TABLE IF NOT EXISTS gasometria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analisis_id INTEGER NOT NULL,
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
    gaso_lactato REAL,
    FOREIGN KEY (analisis_id) REFERENCES analisis(id) ON DELETE CASCADE
);

-- ================== ORINA ===================
CREATE TABLE IF NOT EXISTS orina (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analisis_id INTEGER NOT NULL,
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
    categoria_albuminuria TEXT,
    FOREIGN KEY (analisis_id) REFERENCES analisis(id) ON DELETE CASCADE
);
"""


def create_schema(cursor: Any) -> None:
    cursor.executescript(SCHEMA_SQL)
