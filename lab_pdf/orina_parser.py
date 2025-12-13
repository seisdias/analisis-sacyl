# -*- coding: utf-8 -*-
"""
Parser específico de la sección de ORINA.
Incluye:
- Físico-químico (pH, densidad)
- Tiras reactivas cualitativas (Negativo, +, ++, Trazas, Normal, Indicios...)
- Parámetros cuantitativos (sodio orina, creatinina orina, albúmina, índice alb/cre, categoría)
Robusto frente a asteriscos (*, **) y espaciado irregular típico de PDFs.
"""

from __future__ import annotations

import re
from typing import Dict, Optional, Any

from .pdf_utils import extract_float, extract_token

_NUM = r"([0-9]+(?:[.,][0-9]+)?)"
STAR = r"(?:\s*\*+\s*)?"  # 0 o más asteriscos, con o sin espacios


def _normalize_text(texto: str) -> str:
    if not texto:
        return ""
    t = texto.replace("\u00A0", " ")
    t = t.replace("*", " * ")
    t = re.sub(r"[ \t]+", " ", t)
    t = t.replace("\r\n", "\n").replace("\r", "\n")
    t = re.sub(r"\n{2,}", "\n", t)
    return t


def parse_orina_section(texto: str) -> Dict[str, Any]:
    """
    Extrae datos SOLO de la sección de orina.
    Devuelve un dict con claves estables para BD / tests.
    """
    texto = _normalize_text(texto)

    # ----------------------------
    # Físico-químico
    # ----------------------------
    ph = extract_float(rf"(?im)^\s*pH\s*{STAR}{_NUM}(?=\s|$)", texto)
    densidad = extract_float(rf"(?im)^\s*Densidad\s*{STAR}{_NUM}(?=\s|$)", texto)

    # ----------------------------
    # Tiras reactivas (cualitativos)
    # ----------------------------
    # Ojo: NO usar \b al final si el valor puede ser '+' o '++' (no hay word-boundary).
    token = r"(\+{1,4}|-{1,4}|NEGATIVO|POSITIVO|TRAZAS|NORMAL|INDICIOS|[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+)"

    glucosa = extract_token(rf"(?im)^\s*Glucosa\s*{STAR}{token}(?=\s|$)", texto)
    proteinas = extract_token(rf"(?im)^\s*Prote[ií]nas?\s*{STAR}{token}(?=\s|$)", texto)

    cuerpos_cetonicos = extract_token(
        rf"(?im)^\s*(?:Cuerpos\s+cet[oó]nicos|Acetona)\s*{STAR}{token}(?=\s|$)",
        texto,
    )

    sangre = extract_token(
        rf"(?im)^\s*(?:Sangre|Hemat[ií]es)\s*{STAR}{token}(?=\s|$)",
        texto,
    )

    nitritos = extract_token(rf"(?im)^\s*Nitritos\s*{STAR}{token}(?=\s|$)", texto)

    # Leucocitos: evitar que el token capture "esterasas"
    # - Si aparece "Leucocitos esterasas", consumimos esa palabra
    # - Si NO aparece, impedimos que el token empiece por "esteras..."
    leucocitos_ests = extract_token(
        rf"(?im)^\s*(?:"
        rf"Leucocitos\s+esterasa(?:s)?\s*{STAR}{token}"
        rf"|"
        rf"Leucocitos\s*(?!esterasa(?:s)?\b)\s*{STAR}{token}"
        rf")(?=\s|$)",
        texto,
    )

    bilirrubina = extract_token(rf"(?im)^\s*Bilirrubina\s*{STAR}{token}(?=\s|$)", texto)
    urobilinogeno = extract_token(rf"(?im)^\s*Urobilin[oó]geno\s*{STAR}{token}(?=\s|$)", texto)

    # ----------------------------
    # Cuantitativos
    # ----------------------------
    sodio_ur = extract_float(rf"(?im)^\s*Sodio\s+orina\s*{STAR}{_NUM}(?=\s|$)", texto)
    creatinina_ur = extract_float(rf"(?im)^\s*Creatinina\s+orina\s*{STAR}{_NUM}(?=\s|$)", texto)
    albumina_ur = extract_float(rf"(?im)^\s*Alb[uú]mina\s+orina\s*{STAR}{_NUM}(?=\s|$)", texto)

    # fallback (sin "orina" en la etiqueta)
    if creatinina_ur is None:
        creatinina_ur = extract_float(rf"(?im)^\s*Creatinina\s*{STAR}{_NUM}\s*mg/dL(?=\s|$)", texto)
    if albumina_ur is None:
        albumina_ur = extract_float(rf"(?im)^\s*Alb[uú]mina\s*{STAR}{_NUM}\s*mg/L(?=\s|$)", texto)

    indice_albumina_creatinina = extract_float(
        rf"(?im)^\s*[IÍ]ndice\s+Alb/Cre\s*{STAR}{_NUM}(?=\s|$)",
        texto,
    )

    categoria_albuminuria = extract_token(
        r"(?im)^\s*Categor[ií]a\s+albuminuria\s*\**\s*([A-Z][0-9])(?=\s|$)",
        texto,
    )

    return {
        "ph": ph,
        "densidad": densidad,

        "glucosa": glucosa,
        "proteinas": proteinas,
        "cuerpos_cetonicos": cuerpos_cetonicos,
        "sangre": sangre,
        "nitritos": nitritos,
        "leucocitos_ests": leucocitos_ests,
        "bilirrubina": bilirrubina,
        "urobilinogeno": urobilinogeno,

        "sodio_ur": sodio_ur,
        "creatinina_ur": creatinina_ur,
        "indice_albumina_creatinina": indice_albumina_creatinina,
        "albumina_ur": albumina_ur,
        "categoria_albuminuria": categoria_albuminuria,
    }
