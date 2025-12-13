# -*- coding: utf-8 -*-
"""
Utilidades generales para parsing de informes PDF de laboratorio.
"""

from __future__ import annotations

import re
from typing import Dict, Any, Optional

from pypdf import PdfReader


# ============================================================
#   UTILIDADES GENERALES
# ============================================================

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extrae todo el texto de un PDF en una sola cadena."""
    reader = PdfReader(pdf_path)
    chunks = []
    for page in reader.pages:
        txt = page.extract_text() or ""
        chunks.append(txt)
    return "\n".join(chunks)


def extract_float(pattern: str, texto: str, flags: int = re.IGNORECASE) -> Optional[float]:
    m = re.search(pattern, texto, flags=flags)
    if not m:
        return None
    valor_str = m.group(1).replace(",", ".")
    try:
        return float(valor_str)
    except ValueError:
        return None


def extract_named_value(label: str, texto: str) -> Optional[float]:
    """
    Extrae el primer valor numérico de una línea que empieza por 'label'.
    Tolera asteriscos (*) entre el label y el valor, típicos de valores fuera de rango.
    """
    # ^\s*LABEL\s+(?:\*+\s*)?NUM
    pattern = rf"^\s*{re.escape(label)}\s+(?:\*+\s*)?([+-]?[0-9]+(?:[.,][0-9]+)?)\b"
    m = re.search(pattern, texto, flags=re.MULTILINE)
    if not m:
        return None

    valor_str = m.group(1).replace(",", ".")
    try:
        return float(valor_str)
    except ValueError:
        return None


def extract_token(pattern: str, texto: str) -> Optional[str]:
    """
    Devuelve el primer grupo capturado útil (no None / no vacío) o None.
    Soporta patrones donde el grupo 1 puede no participar.
    """
    m = re.search(pattern, texto, flags=re.IGNORECASE | re.MULTILINE)
    if not m:
        return None

    # Si hay grupos capturados, devuelve el primero "usable"
    if m.lastindex:
        for i in range(1, m.lastindex + 1):
            g = m.group(i)
            if g is not None:
                g = g.strip()
                if g != "":
                    return g
        return None

    # Si no hay grupos, opcionalmente podrías devolver el match completo:
    # return m.group(0).strip()
    return None



def has_any_value(d: Dict[str, Any], ignore_keys: tuple = ()) -> bool:
    """
    Indica si en el dict hay algún valor distinto de None (ignorando ciertas claves).
    """
    return any(
        v is not None
        for k, v in d.items()
        if k not in ignore_keys
    )
