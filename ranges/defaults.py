# ranges/defaults.py
from __future__ import annotations
from typing import Dict
from .models import ParamRange

# -------------------------
#  RANGOS POR DEFECTO
# -------------------------

DEFAULT_PARAM_RANGES: Dict[str, ParamRange] = {
    # ======= BIOQUÍMICA BÁSICA =======
    "glucosa": ParamRange(
        "glucosa", "Glucosa", "Bioquímica — Metabolismo", "mg/dL", 70.0, 110.0
    ),
    "urea": ParamRange(
        "urea", "Urea", "Bioquímica — Metabolismo", "mg/dL", 15.0, 50.0
    ),
    "creatinina": ParamRange(
        "creatinina", "Creatinina", "Bioquímica — Metabolismo", "mg/dL", 0.6, 1.3
    ),

    # ======= ELECTROLITOS / IONES =======
    "calcio": ParamRange(
        "calcio", "Calcio", "Bioquímica — Electrolitos", "mg/dL", 8.4, 10.2
    ),
    "cloro": ParamRange(
        "cloro", "Cloro", "Bioquímica — Electrolitos", "mmol/L", 97.0, 109.0
    ),
    "fosforo": ParamRange(
        "fosforo", "Fósforo", "Bioquímica — Electrolitos", "mg/dL", 2.5, 4.9
    ),
    "potasio": ParamRange(
        "potasio", "Potasio", "Bioquímica — Electrolitos", "mmol/L", 3.5, 5.1
    ),
    "sodio": ParamRange(
        "sodio", "Sodio", "Bioquímica — Electrolitos", "mmol/L", 136.0, 146.0
    ),

    # ======= PERFIL LIPÍDICO =======
    "colesterol_total": ParamRange(
        "colesterol_total", "Colesterol total", "Bioquímica — Lípidos", "mg/dL", 0.0, 200.0
    ),
    "colesterol_hdl": ParamRange(
        "colesterol_hdl", "Colesterol HDL", "Bioquímica — Lípidos", "mg/dL", 40.0, 80.0
    ),
    "colesterol_ldl": ParamRange(
        "colesterol_ldl", "Colesterol LDL", "Bioquímica — Lípidos", "mg/dL", 0.0, 130.0
    ),
    "colesterol_no_hdl": ParamRange(
        "colesterol_no_hdl", "Colesterol no HDL", "Bioquímica — Lípidos", "mg/dL", 0.0, 160.0
    ),
    "trigliceridos": ParamRange(
        "trigliceridos", "Triglicéridos", "Bioquímica — Lípidos", "mg/dL", 0.0, 150.0
    ),
    "indice_riesgo": ParamRange(
        "indice_riesgo", "Índice riesgo", "Bioquímica — Lípidos", "", 0.0, 5.0
    ),

    # ======= HIERRO / VITAMINAS =======
    "hierro": ParamRange(
        "hierro", "Hierro", "Bioquímica — Metabolismo hierro", "µg/dL", 60.0, 170.0
    ),
    "ferritina": ParamRange(
        "ferritina", "Ferritina", "Bioquímica — Metabolismo hierro", "ng/mL", 30.0, 400.0
    ),
    "vitamina_b12": ParamRange(
        "vitamina_b12", "Vitamina B12", "Bioquímica — Vitaminas", "pg/mL", 200.0, 900.0
    ),

    # ======= HEMATOLOGÍA — SERIE BLANCA =======
    "leucocitos": ParamRange(
        "leucocitos", "Leucocitos", "Hematología — Serie blanca", "10³/µL", 4.0, 11.0
    ),
    "neutrofilos_pct": ParamRange(
        "neutrofilos_pct", "Neutrófilos %", "Hematología — Serie blanca", "%", 40.0, 75.0
    ),
    "linfocitos_pct": ParamRange(
        "linfocitos_pct", "Linfocitos %", "Hematología — Serie blanca", "%", 20.0, 45.0
    ),
    "monocitos_pct": ParamRange(
        "monocitos_pct", "Monocitos %", "Hematología — Serie blanca", "%", 2.0, 10.0
    ),
    "eosinofilos_pct": ParamRange(
        "eosinofilos_pct", "Eosinófilos %", "Hematología — Serie blanca", "%", 1.0, 6.0
    ),
    "basofilos_pct": ParamRange(
        "basofilos_pct", "Basófilos %", "Hematología — Serie blanca", "%", 0.0, 2.0
    ),

    "neutrofilos_abs": ParamRange(
        "neutrofilos_abs", "Neutrófilos abs", "Hematología — Serie blanca", "10³/µL", 1.5, 7.5
    ),
    "linfocitos_abs": ParamRange(
        "linfocitos_abs", "Linfocitos abs", "Hematología — Serie blanca", "10³/µL", 1.0, 4.0
    ),
    "monocitos_abs": ParamRange(
        "monocitos_abs", "Monocitos abs", "Hematología — Serie blanca", "10³/µL", 0.2, 1.0
    ),
    "eosinofilos_abs": ParamRange(
        "eosinofilos_abs", "Eosinófilos abs", "Hematología — Serie blanca", "10³/µL", 0.0, 0.5
    ),
    "basofilos_abs": ParamRange(
        "basofilos_abs", "Basófilos abs", "Hematología — Serie blanca", "10³/µL", 0.0, 0.2
    ),

    # ======= HEMATOLOGÍA — SERIE ROJA =======
    "hematies": ParamRange(
        "hematies", "Hematíes", "Hematología — Serie roja", "10⁶/µL", 4.0, 6.0
    ),
    "hemoglobina": ParamRange(
        "hemoglobina", "Hemoglobina", "Hematología — Serie roja", "g/dL", 13.0, 17.5
    ),
    "hematocrito": ParamRange(
        "hematocrito", "Hematocrito", "Hematología — Serie roja", "%", 40.0, 52.0
    ),
    "vcm": ParamRange(
        "vcm", "VCM", "Hematología — Serie roja", "fL", 80.0, 100.0
    ),
    "hcm": ParamRange(
        "hcm", "HCM", "Hematología — Serie roja", "pg", 27.0, 34.0
    ),
    "chcm": ParamRange(
        "chcm", "CHCM", "Hematología — Serie roja", "g/dL", 32.0, 36.0
    ),
    "rdw": ParamRange(
        "rdw", "RDW", "Hematología — Serie roja", "%", 11.0, 15.0
    ),

    # ======= HEMATOLOGÍA — SERIE PLAQUETAR =======
    "plaquetas": ParamRange(
        "plaquetas", "Plaquetas", "Hematología — Serie plaquetar", "10³/µL", 150.0, 450.0
    ),
    "vpm": ParamRange(
        "vpm", "VPM", "Hematología — Serie plaquetar", "fL", 7.0, 12.0
    ),

    # ======= ORINA — CUANTITATIVA =======
    "albumina_ur": ParamRange(
        "albumina_ur", "Albúmina orina", "Orina — Cuantitativa", "mg/L", 0.0, 30.0
    ),
    "creatinina_ur": ParamRange(
        "creatinina_ur", "Creatinina orina", "Orina — Cuantitativa", "mg/dL", 20.0, 300.0
    ),
    "densidad": ParamRange(
        "densidad", "Densidad", "Orina — Cuantitativa", "", 1.005, 1.03
    ),
    "sodio_ur": ParamRange(
        "sodio_ur", "Sodio orina", "Orina — Cuantitativa", "mmol/L", 40.0, 220.0
    ),
    "ph": ParamRange(
        "ph", "pH orina", "Orina — Cuantitativa", "", 5.0, 8.0
    ),
    "indice_albumina_creatinina": ParamRange(
        "indice_albumina_creatinina", "Índice Alb/Cre", "Orina — Cuantitativa", "mg/g", 0.0, 30.0
    ),
}

