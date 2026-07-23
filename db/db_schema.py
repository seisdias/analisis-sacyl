# db/db_schema.py
# -*- coding: utf-8 -*-

from typing import Any

CURRENT_SCHEMA_VERSION: int = 4

SCHEMA_SQL: str = """
-- ================== ANALISIS (DOCUMENTO) ===================
CREATE TABLE IF NOT EXISTS analisis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha_analisis TEXT NOT NULL,
    numero_peticion TEXT,
    origen TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_analisis_fecha_peticion
ON analisis (fecha_analisis, numero_peticion);


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

-- Evitar duplicados: 1 fila por analisis_id en tablas detalle
CREATE UNIQUE INDEX IF NOT EXISTS ux_hematologia_analisis_id ON hematologia(analisis_id);
CREATE UNIQUE INDEX IF NOT EXISTS ux_bioquimica_analisis_id ON bioquimica(analisis_id);
CREATE UNIQUE INDEX IF NOT EXISTS ux_gasometria_analisis_id ON gasometria(analisis_id);
CREATE UNIQUE INDEX IF NOT EXISTS ux_orina_analisis_id ON orina(analisis_id);



-- ================== CONFIG ===================
CREATE TABLE IF NOT EXISTS app_config (
    key TEXT PRIMARY KEY,
    value TEXT
);

-- ================== TRATAMIENTO (CURSO) ===================
CREATE TABLE IF NOT EXISTS treatment_course (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    start_date TEXT,
    end_date TEXT,
    standard_days INTEGER,
    notes TEXT
);

-- ================== INGRESO HOSPITALARIO ===================
CREATE TABLE IF NOT EXISTS hospital_stay (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    admission_date TEXT,
    discharge_date TEXT,
    notes TEXT
);

-- ================== LIMITES POR PARAMETRO ===================
CREATE TABLE IF NOT EXISTS param_limit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    param_key TEXT NOT NULL,
    value REAL NOT NULL,
    label TEXT,
    enabled INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_param_limit_key ON param_limit(param_key);


"""


def create_schema(cursor: Any) -> None:
    for statement in SCHEMA_STATEMENTS:
        cursor.execute(statement)


SCHEMA_STATEMENTS: tuple[str, ...] = tuple(
    statement.strip()
    for statement in SCHEMA_SQL.split(";")
    if statement.strip()
)
