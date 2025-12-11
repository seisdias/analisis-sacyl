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


def extract_float(pattern: str, texto: str, flags: int = 0) -> Optional[float]:
    """
    Aplica un patrón regex y devuelve el primer grupo capturado como float.
    Si no encuentra nada, devuelve None.
    """
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
    Ejemplo de línea:
        Sodio 138 mmol/L 136 - 146
    Buscamos el número inmediatamente después del nombre de la prueba.
    """
    pattern = rf"^{re.escape(label)}\s+([0-9]+(?:[.,][0-9]+)?)\s+"
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
    Devuelve el primer grupo capturado como texto (limpio) o None si no hay match.
    Útil para campos cualitativos (NEGATIVO, TRAZAS, etc.).
    """
    m = re.search(pattern, texto, flags=re.IGNORECASE)
    if not m:
        return None
    return m.group(1).strip()


def has_any_value(d: Dict[str, Any], ignore_keys: tuple = ()) -> bool:
    """
    Indica si en el dict hay algún valor distinto de None (ignorando ciertas claves).
    """
    return any(
        v is not None
        for k, v in d.items()
        if k not in ignore_keys
    )
