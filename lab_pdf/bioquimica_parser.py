# -*- coding: utf-8 -*-
"""
Parser específico de la sección de BIOQUÍMICA (+ perfil lipídico).
Robusto frente a asteriscos (*, **) y espaciado irregular típico de PDFs.
"""

from __future__ import annotations

import re
from typing import Dict, Optional

from .pdf_utils import extract_float


_NUM = r"([0-9]+(?:[.,][0-9]+)?)"
STAR = r"(?:\*\s*)*"  # permite 0..N asteriscos, con espacios opcionales


def _normalize_text(texto: str) -> str:
    if not texto:
        return ""
    t = texto.replace("\u00A0", " ")  # NBSP
    # separa asteriscos para que '**' sea '* *'
    t = t.replace("*", " * ")
    t = re.sub(r"[ \t]+", " ", t)
    t = t.replace("\r\n", "\n").replace("\r", "\n")
    t = re.sub(r"\n{2,}", "\n", t)
    return t


def parse_bioquimica_section(texto: str) -> Dict[str, Optional[float]]:
    """
    Extrae parámetros de bioquímica / perfil lipídico a partir del texto
    de la sección de BIOQUÍMICA (y PERFIL LIPÍDICO si aparece).
    """
    texto = _normalize_text(texto)

    data: Dict[str, Optional[float]] = {}

    # Básicos
    data["glucosa"] = extract_float(rf"Glucosa\s*{STAR}{_NUM}\s+", texto)
    data["urea"] = extract_float(rf"Urea\s*{STAR}{_NUM}\s+", texto)
    data["creatinina"] = extract_float(rf"Creatinina\s*{STAR}{_NUM}\s+", texto)

    data["sodio"] = extract_float(rf"Sodio\s*{STAR}{_NUM}\s+", texto)
    data["potasio"] = extract_float(rf"Potasio\s*{STAR}{_NUM}\s+", texto)

    # Cloro / Cloruro
    data["cloro"] = extract_float(
        rf"(?:Cloro|Cloruro)\s*{STAR}{_NUM}\s+",
        texto,
    )

    # Calcio / Fosfato-Fósforo
    data["calcio"] = extract_float(rf"Calcio\s*{STAR}{_NUM}\s+mg\s*/\s*dL", texto)
    data["fosfato"] = extract_float(
        rf"(?:Fosfato|F[oó]sforo)\s*{STAR}{_NUM}\s+",
        texto,
    )

    # Otros frecuentes
    data["acido_urico"] = extract_float(
        rf"[Aa]cido\s+u[rú]rico\s*{STAR}{_NUM}\s+",
        texto,
    )
    data["proteinas_totales"] = extract_float(
        rf"Prote[ií]nas\s+totales\s*{STAR}{_NUM}\s+",
        texto,
    )

    data["ast_got"] = extract_float(
        rf"Aspartato\s+aminotransferasa\s*\(AST\s*/\s*GOT\)\s*{STAR}{_NUM}\s+",
        texto,
    )
    data["alt_gpt"] = extract_float(
        rf"Alanina\s+aminotransferasa\s*\(ALT\s*/\s*GPT\)\s*{STAR}{_NUM}\s+",
        texto,
    )
    data["ggt"] = extract_float(
        rf"Gammaglutamil\s+transferasa\s*\(GGT\)\s*{STAR}{_NUM}\s+",
        texto,
    )
    data["bilirrubina_total"] = extract_float(
        rf"Bilirrubina\s+Total\s*{STAR}{_NUM}\s+",
        texto,
    )
    data["fosfatasa_alcalina"] = extract_float(
        rf"Fosfatasa\s+alcalina\s*{STAR}{_NUM}\s+",
        texto,
    )
    data["ldh"] = extract_float(
        rf"Lactato\s+deshidrogenasa\s*\(LDH\)\s*{STAR}{_NUM}\s+",
        texto,
    )
    data["magnesio"] = extract_float(
        rf"Magnesio\s*{STAR}{_NUM}\s+",
        texto,
    )
    data["pcr"] = extract_float(
        rf"Prote[ií]na\s+C\s+reactiva\s*{STAR}{_NUM}\s+",
        texto,
    )

    # Perfil lipídico
    data["colesterol_total"] = extract_float(
        rf"Colesterol\s+total\s*{STAR}{_NUM}\s+",
        texto,
    )
    data["trigliceridos"] = extract_float(
        rf"Triglic[eé]ridos\s*{STAR}{_NUM}\s+",
        texto,
    )

    return data
