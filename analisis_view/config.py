# analisis_view/config.py
# -*- coding: utf-8 -*-

from __future__ import annotations
from typing import Dict, List

# -------------------- FIELDS --------------------

HEMA_FIELDS: List[str] = [
    "id",
    "fecha_analisis",
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

BIOQ_FIELDS: List[str] = [
    "id",
    "fecha_analisis",
    "numero_peticion",
    "glucosa",
    "urea",
    "creatinina",
    "sodio",
    "potasio",
    "cloro",
    "calcio",
    "fosforo",
    "colesterol_total",
    "colesterol_hdl",
    "colesterol_ldl",
    "colesterol_no_hdl",
    "trigliceridos",
    "indice_riesgo",
    "hierro",
    "ferritina",
    "vitamina_b12",
]

ORINA_FIELDS: List[str] = [
    "id",
    "fecha_analisis",
    "numero_peticion",
    "color",
    "aspecto",
    "ph",
    "densidad",
    "glucosa",
    "proteinas",
    "cuerpos_cetonicos",
    "sangre",
    "nitritos",
    "leucocitos_ests",
    "bilirrubina",
    "urobilinogeno",
    "sodio_ur",
    "creatinina_ur",
    "indice_albumina_creatinina",
    "categoria_albuminuria",
    "albumina_ur",
]

# -------------------- VISIBLE_FIELDS --------------------

# Ahora SOLO ocultamos 'id'. 'origen' vuelve a ser columna visible.
HEMA_VISIBLE_FIELDS: List[str] = [
    f for f in HEMA_FIELDS if f not in ("id",)
]

BIOQ_VISIBLE_FIELDS: List[str] = [
    f for f in BIOQ_FIELDS if f not in ("id",)
]

ORINA_VISIBLE_FIELDS: List[str] = [
    f for f in ORINA_FIELDS if f not in ("id",)
]

# -------------------- HEADERS --------------------

HEMA_HEADERS: Dict[str, str] = {
    "fecha_analisis": "Fecha",
    "numero_peticion": "Nº petición",
    "origen": "Origen",
    "leucocitos": "Leucocitos (10³/µL)",
    "neutrofilos_pct": "Neutrófilos %",
    "linfocitos_pct": "Linfocitos %",
    "monocitos_pct": "Monocitos %",
    "eosinofilos_pct": "Eosinófilos %",
    "basofilos_pct": "Basófilos %",
    "neutrofilos_abs": "Neutrófilos abs (10³/µL)",
    "linfocitos_abs": "Linfocitos abs (10³/µL)",
    "monocitos_abs": "Monocitos abs (10³/µL)",
    "eosinofilos_abs": "Eosinófilos abs (10³/µL)",
    "basofilos_abs": "Basófilos abs (10³/µL)",
    "hematies": "Hematíes (10⁶/µL)",
    "hemoglobina": "Hemoglobina (g/dL)",
    "hematocrito": "Hematocrito (%)",
    "vcm": "VCM (fL)",
    "hcm": "HCM (pg)",
    "chcm": "CHCM (g/dL)",
    "rdw": "RDW (%)",
    "plaquetas": "Plaquetas (10³/µL)",
    "vpm": "VPM (fL)",
}

BIOQ_HEADERS: Dict[str, str] = {
    "fecha_analisis": "Fecha",
    "numero_peticion": "Nº petición",
    "glucosa": "Glucosa",
    "urea": "Urea",
    "creatinina": "Creatinina",
    "sodio": "Sodio",
    "potasio": "Potasio",
    "cloro": "Cloro",
    "calcio": "Calcio",
    "fosforo": "Fósforo",
    "colesterol_total": "Colesterol total",
    "colesterol_hdl": "Colesterol HDL",
    "colesterol_ldl": "Colesterol LDL",
    "colesterol_no_hdl": "Colesterol no HDL",
    "trigliceridos": "Triglicéridos",
    "indice_riesgo": "Índice riesgo",
    "hierro": "Hierro",
    "ferritina": "Ferritina",
    "vitamina_b12": "Vitamina B12",
}

ORINA_HEADERS: Dict[str, str] = {
    "fecha_analisis": "Fecha",
    "numero_peticion": "Nº petición",
    "color": "Color",
    "aspecto": "Aspecto",
    "ph": "pH",
    "densidad": "Densidad",
    "glucosa": "Glucosa (tira)",
    "proteinas": "Proteínas",
    "cuerpos_cetonicos": "Cuerpos cetónicos",
    "sangre": "Sangre",
    "nitritos": "Nitritos",
    "leucocitos_ests": "Leucocitos est.",
    "bilirrubina": "Bilirrubina",
    "urobilinogeno": "Urobilinógeno",
    "sodio_ur": "Sodio orina",
    "creatinina_ur": "Creatinina orina",
    "indice_albumina_creatinina": "Índice Alb/Cre",
    "categoria_albuminuria": "Cat. albuminuria",
    "albumina_ur": "Albúmina orina",
}
