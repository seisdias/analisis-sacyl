# -*- coding: utf-8 -*-
"""
Parser específico de la sección de BIOQUÍMICA (+ perfil lipídico).
"""

from __future__ import annotations

from typing import Dict, Optional

from .pdf_utils import extract_float


def parse_bioquimica_section(texto: str) -> Dict[str, Optional[float]]:
    """
    Extrae parámetros de bioquímica / perfil lipídico a partir del texto
    de la sección de BIOQUÍMICA (y PERFIL LIPÍDICO si aparece).
    """
    data: Dict[str, Optional[float]] = {}

    # Valores básicos
    data["glucosa"] = extract_float(r"Glucosa\s+\**([0-9]+(?:[.,][0-9]+)?)\s+", texto)
    data["urea"] = extract_float(r"Urea\s+\**([0-9]+(?:[.,][0-9]+)?)\s+", texto)
    data["creatinina"] = extract_float(r"Creatinina\s+\**([0-9]+(?:[.,][0-9]+)?)\s+", texto)

    data["sodio"] = extract_float(r"Sodio\s+\**([0-9]+(?:[.,][0-9]+)?)\s+", texto)
    data["potasio"] = extract_float(r"Potasio\s+\**([0-9]+(?:[.,][0-9]+)?)\s+", texto)

    # En los informes reales es "Cloruro"
    data["cloruro"] = extract_float(r"Cloruro\s+\**([0-9]+(?:[.,][0-9]+)?)\s+", texto)

    # Calcio / Fosfato (puede aparecer como Fosfato/Fósforo/Fosforo)
    data["calcio"] = extract_float(r"Calcio\s+\**([0-9]+(?:[.,][0-9]+)?)\s+mg/dL", texto)
    data["fosfato"] = extract_float(
        r"(?:Fosfato|Fósforo|Fosforo)\s+\**([0-9]+(?:[.,][0-9]+)?)\s+",
        texto,
    )

    # Otros parámetros frecuentes
    data["acido_urico"] = extract_float(
        r"Acido úrico\s+\**([0-9]+(?:[.,][0-9]+)?)\s+", texto
    )
    data["proteinas_totales"] = extract_float(
        r"Proteínas totales\s+\**([0-9]+(?:[.,][0-9]+)?)\s+", texto
    )

    data["ast_got"] = extract_float(
        r"Aspartato aminotransferasa \(AST/GOT\)\s+\**([0-9]+(?:[.,][0-9]+)?)\s+",
        texto,
    )
    data["alt_gpt"] = extract_float(
        r"Alanina aminotransferasa \(ALT/GPT\)\s+\**([0-9]+(?:[.,][0-9]+)?)\s+",
        texto,
    )
    data["ggt"] = extract_float(
        r"Gammaglutamil transferasa \(GGT\)\s+\**([0-9]+(?:[.,][0-9]+)?)\s+",
        texto,
    )
    data["bilirrubina_total"] = extract_float(
        r"Bilirrubina Total\s+\**([0-9]+(?:[.,][0-9]+)?)\s+",
        texto,
    )
    data["fosfatasa_alcalina"] = extract_float(
        r"Fosfatasa alcalina\s+\**([0-9]+(?:[.,][0-9]+)?)\s+",
        texto,
    )
    data["ldh"] = extract_float(
        r"Lactato deshidrogenasa \(LDH\)\s+\**([0-9]+(?:[.,][0-9]+)?)\s+",
        texto,
    )
    data["magnesio"] = extract_float(
        r"Magnesio\s+\**([0-9]+(?:[.,][0-9]+)?)\s+",
        texto,
    )
    data["pcr"] = extract_float(
        r"Proteína C reactiva\s+\**([0-9]+(?:[.,][0-9]+)?)\s+",
        texto,
    )

    # Perfil lipídico
    data["colesterol_total"] = extract_float(
        r"Colesterol total\s+\**([0-9]+(?:[.,][0-9]+)?)\s+",
        texto,
    )
    data["trigliceridos"] = extract_float(
        r"Triglicéridos\s+\**([0-9]+(?:[.,][0-9]+)?)\s+",
        texto,
    )

    return data
