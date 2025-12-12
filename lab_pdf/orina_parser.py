# -*- coding: utf-8 -*-
"""
Parser específico de la sección de ORINA.
Incluye:
- Físico-químico (pH, densidad)
- Tiras reactivas cualitativas (NEGATIVO, +, ++, TRAZAS, NORMAL...)
- Parámetros cuantitativos (sodio orina, creatinina orina, albúmina, índice alb/cre, categoría)
Robusto frente a asteriscos (*, **) y espaciado irregular típico de PDFs.
"""

from __future__ import annotations

import re
from typing import Dict, Optional, Any

from .pdf_utils import extract_float, extract_token


_NUM = r"([0-9]+(?:[.,][0-9]+)?)"
STAR = r"(?:\*\s*)*"


def _normalize_text(texto: str) -> str:
    if not texto:
        return ""
    t = texto.replace("\u00A0", " ")
    t = t.replace("*", " * ")
    t = re.sub(r"[ \t]+", " ", t)
    t = t.replace("\r\n", "\n").replace("\r", "\n")
    t = re.sub(r"\n{2,}", "\n", t)
    return t


def _extract_int(pattern: str, texto: str) -> Optional[int]:
    val = extract_float(pattern, texto)
    if val is None:
        return None
    try:
        return int(round(val))
    except Exception:
        return None


def parse_orina_section(texto: str) -> Dict[str, Any]:
    """
    Extrae datos SOLO de la sección de orina.
    Devuelve un dict con claves estables para BD / tests.
    """
    texto = _normalize_text(texto)

    # ----------------------------
    # Físico-químico
    # ----------------------------
    ph = extract_float(rf"\bpH\s*{STAR}{_NUM}\b", texto)
    densidad = _extract_int(rf"\bDensidad\s*{STAR}{_NUM}\b", texto)

    # ----------------------------
    # Tiras reactivas (cualitativos)
    # ----------------------------
    # token: permitimos palabras (NEGATIVO/TRAZAS/NORMAL...) y +, ++, +++
    token = r"([A-ZÁÉÍÓÚÜÑ]+|TRAZAS|NEGATIVO|NORMAL|\+{1,4})"

    glucosa = extract_token(rf"\bGlucosa\b\s*{STAR}{token}", texto)
    proteinas = extract_token(rf"\bProte[ií]nas\b\s*{STAR}{token}", texto)
    cuerpos_cetonicos = extract_token(rf"\bCuerpos\s+cet[oó]nicos\b\s*{STAR}{token}", texto)
    sangre = extract_token(rf"\bSangre\b\s*{STAR}{token}", texto)
    nitritos = extract_token(rf"\bNitritos\b\s*{STAR}{token}", texto)

    # “Leucocitos esterasas” (a veces “esterasa” / “esterasas”)
    leucocitos_ests = extract_token(
        rf"\bLeucocitos\s+esteras(?:a|as)?\b\s*{STAR}{token}",
        texto,
    )

    bilirrubina = extract_token(rf"\bBilirrubina\b\s*{STAR}{token}", texto)
    urobilinogeno = extract_token(rf"\bUrobilin[oó]geno\b\s*{STAR}{token}", texto)

    # ----------------------------
    # Cuantitativos
    # ----------------------------
    sodio_ur = extract_float(rf"\bSodio\s+orina\b\s*{STAR}{_NUM}\b", texto)
    creatinina_ur = extract_float(rf"\bCreatinina\s+orina\b\s*{STAR}{_NUM}\b", texto)
    indice_albumina_creatinina = extract_float(
        rf"\b[IÍ]ndice\s+Alb/Cre\b\s*{STAR}{_NUM}\b",
        texto,
    )
    albumina_ur = extract_float(rf"\bAlb[uú]mina\s+orina\b\s*{STAR}{_NUM}\b", texto)

    categoria_albuminuria = extract_token(
        r"\bCategor[ií]a\s+albuminuria\b\s*\**\s*([A-Z][0-9])\b",
        texto,
    )

    return {
        # físico-químico
        "ph": ph,
        "densidad": densidad,

        # tiras (cualitativos)
        "glucosa": glucosa,
        "proteinas": proteinas,
        "cuerpos_cetonicos": cuerpos_cetonicos,
        "sangre": sangre,
        "nitritos": nitritos,
        "leucocitos_ests": leucocitos_ests,
        "bilirrubina": bilirrubina,
        "urobilinogeno": urobilinogeno,

        # cuantitativos (CLAVES BD/TEST)
        "sodio_ur": sodio_ur,
        "creatinina_ur": creatinina_ur,
        "indice_albumina_creatinina": indice_albumina_creatinina,
        "albumina_ur": albumina_ur,
        "categoria_albuminuria": categoria_albuminuria,
    }
