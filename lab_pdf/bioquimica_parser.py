# -*- coding: utf-8 -*-
"""
Parser específico de la sección de BIOQUÍMICA.
"""

from __future__ import annotations

import re
from typing import Dict, Optional

from .pdf_utils import extract_float


def parse_bioquimica_section(texto: str) -> Dict[str, Optional[float]]:
    """
    Extrae parámetros de bioquímica a partir del texto de la sección.
    Robusto ante asteriscos (*) y variaciones de etiquetas.
    """

    # Asteriscos opcionales ANTES del valor (con espacios opcionales alrededor)
    AST = r"(?:\s*\*+\s*)?"  # 0 o más asteriscos

    flags = re.IGNORECASE

    # -------------------------
    # Básicos
    # -------------------------
    glucosa = extract_float(
        rf"\bGlucosa\b\s*{AST}([0-9]+(?:[.,][0-9]+)?)\s*mg/dL",
        texto,
        flags=flags,
    )
    urea = extract_float(
        rf"\bUrea\b\s*{AST}([0-9]+(?:[.,][0-9]+)?)\s*mg/dL",
        texto,
        flags=flags,
    )
    creatinina = extract_float(
        rf"\bCreatinina\b\s*{AST}([0-9]+(?:[.,][0-9]+)?)\s*mg/dL",
        texto,
        flags=flags,
    )

    sodio = extract_float(
        rf"\bSodio\b\s*{AST}([0-9]+(?:[.,][0-9]+)?)\s*mmol/L",
        texto,
        flags=flags,
    )
    potasio = extract_float(
        rf"\bPotasio\b\s*{AST}([0-9]+(?:[.,][0-9]+)?)\s*mmol/L",
        texto,
        flags=flags,
    )

    # En tus PDFs sale como "Cloruro" (a veces podría salir "Cloro")
    cloro = extract_float(
        rf"\bClor(?:o|uro)\b\s*{AST}([0-9]+(?:[.,][0-9]+)?)\s*mmol/L",
        texto,
        flags=flags,
    )

    calcio = extract_float(
        rf"\bCalcio\b\s*{AST}([0-9]+(?:[.,][0-9]+)?)\s*mg/dL",
        texto,
        flags=flags,
    )

    # A veces sale "Fósforo", otras "Fosfato"
    fosforo = extract_float(
        rf"\b(?:F[oó]sforo|Fosfato)\b\s*{AST}([0-9]+(?:[.,][0-9]+)?)\s*mg/dL",
        texto,
        flags=flags,
    )

    acido_urico = extract_float(
        rf"\b[ÁA]cido\s+úrico\b\s*{AST}([0-9]+(?:[.,][0-9]+)?)\s*mg/dL",
        texto,
        flags=flags,
    )

    # "Gammaglutamil transferasa (GGT)" o "GGT"
    ggt = extract_float(
        rf"(?:\bGGT\b|Gammaglutamil\s+transferasa\s*\(\s*GGT\s*\))\s*{AST}([0-9]+(?:[.,][0-9]+)?)\s*U/L",
        texto,
        flags=flags,
    )

    # "Alanina aminotransferasa (ALT/GPT)" o variantes
    alt_gpt = extract_float(
        rf"(?:\bALT\b|Alanina\s+aminotransferasa\s*\(\s*ALT\s*/\s*GPT\s*\)|ALT\s*/\s*GPT|ALT\s*\(\s*GPT\s*\))\s*{AST}([0-9]+(?:[.,][0-9]+)?)\s*U/L",
        texto,
        flags=flags,
    )

    # "Aspartato aminotransferasa (AST/GOT)" o variantes
    ast_got = extract_float(
        rf"(?:\bAST\b|Aspartato\s+aminotransferasa\s*\(\s*AST\s*/\s*GOT\s*\)|AST\s*/\s*GOT|AST\s*\(\s*GOT\s*\))\s*{AST}([0-9]+(?:[.,][0-9]+)?)\s*U/L",
        texto,
        flags=flags,
    )

    fosfatasa_alcalina = extract_float(
        rf"\bFosfatasa\s+alcalina\b\s*{AST}([0-9]+(?:[.,][0-9]+)?)\s*U/L",
        texto,
        flags=flags,
    )

    bilirrubina_total = extract_float(
        rf"\bBilirrubina\s+total\b\s*{AST}([0-9]+(?:[.,][0-9]+)?)\s*mg/dL",
        texto,
        flags=flags,
    )

    # -------------------------
    # Lípidos (lo que te falta)
    # -------------------------
    colesterol_total = extract_float(
        rf"\bColesterol\s+total\b\s*{AST}([0-9]+(?:[.,][0-9]+)?)\s*mg/dL",
        texto,
        flags=flags,
    )
    colesterol_hdl = extract_float(
        rf"\bColesterol\s+HDL\b\s*{AST}([0-9]+(?:[.,][0-9]+)?)\s*mg/dL",
        texto,
        flags=flags,
    )
    colesterol_ldl = extract_float(
        rf"\bColesterol\s+LDL\b\s*{AST}([0-9]+(?:[.,][0-9]+)?)\s*mg/dL",
        texto,
        flags=flags,
    )
    colesterol_no_hdl = extract_float(
        rf"\bColesterol\s+no\s+HDL\b\s*{AST}([0-9]+(?:[.,][0-9]+)?)\s*mg/dL",
        texto,
        flags=flags,
    )
    trigliceridos = extract_float(
        rf"\bTriglic[eé]ridos\b\s*{AST}([0-9]+(?:[.,][0-9]+)?)\s*mg/dL",
        texto,
        flags=flags,
    )

    # Índice de riesgo cardiovascular
    indice_riesgo = extract_float(
        rf"\b[ÍI]ndice\s+de\s+riesgo\s+cardiovascular\b\s*{AST}([0-9]+(?:[.,][0-9]+)?)",
        texto,
        flags=flags,
    )

    # -------------------------
    # Hierro / Ferritina / Vitaminas
    # -------------------------
    hierro = extract_float(
        rf"\bHierro\b\s*{AST}([0-9]+(?:[.,][0-9]+)?)\s*µ?g/dL",
        texto,
        flags=flags,
    )
    ferritina = extract_float(
        rf"\bFerritina\b\s*{AST}([0-9]+(?:[.,][0-9]+)?)\s*ng/mL",
        texto,
        flags=flags,
    )
    vitamina_b12 = extract_float(
        rf"\bVitamina\s+B12\b\s*{AST}([0-9]+(?:[.,][0-9]+)?)\s*pg/mL",
        texto,
        flags=flags,
    )
    folico = extract_float(
        rf"\b[ÁA]cido\s+f[oó]lico\b\s*{AST}([0-9]+(?:[.,][0-9]+)?)\s*ng/mL",
        texto,
        flags=flags,
    )

    return {
        "glucosa": glucosa,
        "urea": urea,
        "creatinina": creatinina,
        "sodio": sodio,
        "potasio": potasio,
        "cloro": cloro,
        "calcio": calcio,
        "fosforo": fosforo,
        "acido_urico": acido_urico,
        "ggt": ggt,
        "alt_gpt": alt_gpt,
        "ast_got": ast_got,
        "fosfatasa_alcalina": fosfatasa_alcalina,
        "bilirrubina_total": bilirrubina_total,
        "colesterol_total": colesterol_total,
        "colesterol_hdl": colesterol_hdl,
        "colesterol_ldl": colesterol_ldl,
        "colesterol_no_hdl": colesterol_no_hdl,
        "trigliceridos": trigliceridos,
        "indice_riesgo": indice_riesgo,
        "hierro": hierro,
        "ferritina": ferritina,
        "vitamina_b12": vitamina_b12,
        "folico": folico,
    }
