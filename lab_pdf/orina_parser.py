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
    # separa * para que regex tipo "Label * 1.23" funcione aunque venga pegado
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
    ph = extract_float(rf"(?im)^\s*pH\s*{STAR}{_NUM}\b", texto)
    densidad = extract_float(rf"(?im)^\s*Densidad\s*{STAR}{_NUM}\b", texto)

    # ----------------------------
    # Tiras reactivas (cualitativos)
    # ----------------------------
    # Permitimos:
    # - palabras (Negativo, Normal, Indicios, Trazas, etc.)
    # - + / ++ / +++
    # - --- / -- / -
    token = r"([A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+|TRAZAS|NEGATIVO|NORMAL|INDICIOS|\+{1,4}|-{1,4})"

    # Importante: extract_token usa re.search(pattern, ..., flags?)
    # como no controlamos flags ahí, metemos (?i) dentro para IGNORECASE
    glucosa = extract_token(rf"(?im)^\s*Glucosa\s*{STAR}{token}\b", texto)
    proteinas = extract_token(rf"(?im)^\s*Prote[ií]nas\s*{STAR}{token}\b", texto)

    # Cuerpos cetónicos puede aparecer como "Cuerpos cetónicos" o "Acetona"
    cuerpos_cetonicos = extract_token(
        rf"(?im)^\s*(?:Cuerpos\s+cet[oó]nicos|Acetona)\s*{STAR}{token}\b",
        texto,
    )

    # Sangre puede aparecer como "Sangre" o "Hematíes"
    sangre = extract_token(
        rf"(?im)^\s*(?:Sangre|Hemat[ií]es)\s*{STAR}{token}\b",
        texto,
    )

    nitritos = extract_token(rf"(?im)^\s*Nitritos\s*{STAR}{token}\b", texto)

    # Leucocitos: en algunos informes sale solo "Leucocitos" y en otros "Leucocitos esterasas"
    leucocitos_ests = extract_token(
        rf"(?im)^\s*Leucocitos(?:\s+esteras(?:a|as)?)?\s*{STAR}{token}\b",
        texto,
    )

    bilirrubina = extract_token(rf"(?im)^\s*Bilirrubina\s*{STAR}{token}\b", texto)
    urobilinogeno = extract_token(rf"(?im)^\s*Urobilin[oó]geno\s*{STAR}{token}\b", texto)

    # ----------------------------
    # Cuantitativos
    # ----------------------------
    # ----------------------------
    # Cuantitativos
    # ----------------------------
    # En algunos informes viene como:
    #   "Sodio orina 140 mmol/L ..."
    # pero en "Bioquímica en orina 1 micción" suele venir solo:
    #   "Creatinina 218 mg/dL ..."
    #   "Albúmina <7 mg/L ..."
    #
    # 1) Intento "xxx orina"
    sodio_ur = extract_float(rf"(?im)^\s*Sodio\s+orina\s*{STAR}{_NUM}\b", texto)
    creatinina_ur = extract_float(rf"(?im)^\s*Creatinina\s+orina\s*{STAR}{_NUM}\b", texto)
    albumina_ur = extract_float(rf"(?im)^\s*Alb[uú]mina\s+orina\s*{STAR}{_NUM}\b", texto)

    # 2) Fallback: si estamos dentro del bloque "BIOQUÍMICA EN ORINA", aceptar etiqueta sin "orina"
    if creatinina_ur is None:
        creatinina_ur = extract_float(rf"(?im)^\s*Creatinina\s*{STAR}{_NUM}\s*mg/dL\b", texto)

    # Albúmina puede venir como "<7", en ese caso extract_float no captura (bien) → se queda en None.
    if albumina_ur is None:
        albumina_ur = extract_float(rf"(?im)^\s*Alb[uú]mina\s*{STAR}{_NUM}\s*mg/L\b", texto)

    # Índice Alb/Cre (si aparece explícito)
    indice_albumina_creatinina = extract_float(
        rf"(?im)^\s*[IÍ]ndice\s+Alb/Cre\s*{STAR}{_NUM}\b",
        texto,
    )

    categoria_albuminuria = extract_token(
        r"(?im)^\s*Categor[ií]a\s+albuminuria\s*\**\s*([A-Z][0-9])\b",
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
