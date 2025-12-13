# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Dict, List, Tuple


# Mapa: nombre_parametro -> {"table": ..., "label": ...}
PARAM_DEFS: Dict[str, Dict[str, str]] = {
    # ---- HEMATOLOGÍA ----
    "leucocitos":        {"table": "hematologia", "label": "Leucocitos"},
    "neutrofilos_pct":   {"table": "hematologia", "label": "Neutrófilos (%)"},
    "linfocitos_pct":    {"table": "hematologia", "label": "Linfocitos (%)"},
    "monocitos_pct":     {"table": "hematologia", "label": "Monocitos (%)"},
    "eosinofilos_pct":   {"table": "hematologia", "label": "Eosinófilos (%)"},
    "basofilos_pct":     {"table": "hematologia", "label": "Basófilos (%)"},
    "neutrofilos_abs":   {"table": "hematologia", "label": "Neutrófilos (abs)"},
    "linfocitos_abs":    {"table": "hematologia", "label": "Linfocitos (abs)"},
    "monocitos_abs":     {"table": "hematologia", "label": "Monocitos (abs)"},
    "eosinofilos_abs":   {"table": "hematologia", "label": "Eosinófilos (abs)"},
    "basofilos_abs":     {"table": "hematologia", "label": "Basófilos (abs)"},
    "hematies":          {"table": "hematologia", "label": "Hematíes"},
    "hemoglobina":       {"table": "hematologia", "label": "Hemoglobina"},
    "hematocrito":       {"table": "hematologia", "label": "Hematocrito"},
    "vcm":               {"table": "hematologia", "label": "VCM"},
    "hcm":               {"table": "hematologia", "label": "HCM"},
    "chcm":              {"table": "hematologia", "label": "CHCM"},
    "rdw":               {"table": "hematologia", "label": "RDW"},
    "plaquetas":         {"table": "hematologia", "label": "Plaquetas"},
    "vpm":               {"table": "hematologia", "label": "VPM"},

    # ---- BIOQUÍMICA ----
    "glucosa":                   {"table": "bioquimica", "label": "Glucosa"},
    "urea":                      {"table": "bioquimica", "label": "Urea"},
    "creatinina":                {"table": "bioquimica", "label": "Creatinina"},
    "sodio":                     {"table": "bioquimica", "label": "Sodio"},
    "potasio":                   {"table": "bioquimica", "label": "Potasio"},
    "cloro":                     {"table": "bioquimica", "label": "Cloro"},
    "calcio":                    {"table": "bioquimica", "label": "Calcio"},
    "fosforo":                   {"table": "bioquimica", "label": "Fósforo"},
    "colesterol_total":          {"table": "bioquimica", "label": "Colesterol total"},
    "colesterol_hdl":            {"table": "bioquimica", "label": "Colesterol HDL"},
    "colesterol_ldl":            {"table": "bioquimica", "label": "Colesterol LDL"},
    "colesterol_no_hdl":         {"table": "bioquimica", "label": "Colesterol no HDL"},
    "trigliceridos":             {"table": "bioquimica", "label": "Triglicéridos"},
    "indice_riesgo":             {"table": "bioquimica", "label": "Índice de riesgo"},
    "hierro":                    {"table": "bioquimica", "label": "Hierro"},
    "ferritina":                 {"table": "bioquimica", "label": "Ferritina"},
    "vitamina_b12":              {"table": "bioquimica", "label": "Vitamina B12"},

    # ---- GASOMETRÍA ----
    "gaso_ph":           {"table": "gasometria", "label": "pH (gaso)"},
    "gaso_pco2":         {"table": "gasometria", "label": "pCO₂"},
    "gaso_po2":          {"table": "gasometria", "label": "pO₂"},
    "gaso_tco2":         {"table": "gasometria", "label": "CO₂ total (TCO₂)"},
    "gaso_so2_calc":     {"table": "gasometria", "label": "sO₂ calc."},
    "gaso_so2":          {"table": "gasometria", "label": "sO₂ medida"},
    "gaso_p50":          {"table": "gasometria", "label": "p50"},
    "gaso_bicarbonato":  {"table": "gasometria", "label": "Bicarbonato"},
    "gaso_sbc":          {"table": "gasometria", "label": "Bicarbonato estándar (SBC)"},
    "gaso_eb":           {"table": "gasometria", "label": "Exceso de bases (EB)"},
    "gaso_beecf":        {"table": "gasometria", "label": "Exceso bases ECF (BEecf)"},
    "gaso_lactato":      {"table": "gasometria", "label": "Lactato"},

    # ---- ORINA ----
    "ph":                         {"table": "orina", "label": "pH orina"},
    "densidad":                   {"table": "orina", "label": "Densidad orina"},
    "sodio_ur":                   {"table": "orina", "label": "Sodio orina"},
    "creatinina_ur":              {"table": "orina", "label": "Creatinina orina"},
    "indice_albumina_creatinina": {"table": "orina", "label": "Índice Alb/Cre"},
    "albumina_ur":                {"table": "orina", "label": "Albúmina orina"},
}


# Grupos para checkboxes: (título_grupo, [param_names...])
PARAM_GROUPS: List[Tuple[str, List[str]]] = [
    ("Hemograma", [
        "leucocitos", "hematies", "hemoglobina", "hematocrito", "vcm", "hcm", "chcm", "rdw",
        "plaquetas", "vpm",
        "neutrofilos_pct", "linfocitos_pct", "monocitos_pct", "eosinofilos_pct", "basofilos_pct",
        "neutrofilos_abs", "linfocitos_abs", "monocitos_abs", "eosinofilos_abs", "basofilos_abs",
    ]),
    ("Bioquímica", [
        "glucosa", "urea", "creatinina", "sodio", "potasio", "cloro", "calcio", "fosforo",
        "colesterol_total", "colesterol_hdl", "colesterol_ldl", "colesterol_no_hdl",
        "trigliceridos", "indice_riesgo", "hierro", "ferritina", "vitamina_b12",
    ]),
    ("Gasometría", [
        "gaso_ph", "gaso_pco2", "gaso_po2", "gaso_tco2", "gaso_so2_calc", "gaso_so2",
        "gaso_p50", "gaso_bicarbonato", "gaso_sbc", "gaso_eb", "gaso_beecf", "gaso_lactato",
    ]),
    ("Orina cuantitativa", [
        "ph", "densidad", "sodio_ur", "creatinina_ur", "indice_albumina_creatinina", "albumina_ur",
    ]),
]
