# -*- coding: utf-8 -*-
"""
Localización y separación de secciones del informe (HEMATOLOGÍA, BIOQUÍMICA, etc.).
"""

from __future__ import annotations

import re
from typing import Dict


SECTION_PATTERNS = {
    "hematologia": r"HEMATOLOGÍA",
    "bioquimica": r"BIOQUÍMICA",
    "gasometria": r"GASOMETRÍA",
    # Para orina, usaremos cualquier encabezado que contenga ORINA.
    "orina": r"\bORINA\b",
}


def split_lab_sections(text: str) -> Dict[str, str]:
    """
    Busca encabezados tipo 'HEMATOLOGÍA', 'BIOQUÍMICA', 'GASOMETRÍA', 'ORINA'
    y devuelve un dict con el texto parcial de cada sección.

    Si no se encuentra una sección, simplemente no aparecerá en el dict.
    """
    markers = []

    for key, pat in SECTION_PATTERNS.items():
        m = re.search(pat, text)
        if m:
            markers.append((m.start(), key))

    if not markers:
        return {}

    markers.sort(key=lambda t: t[0])

    sections: Dict[str, str] = {}
    for idx, (start_pos, key) in enumerate(markers):
        end_pos = markers[idx + 1][0] if idx + 1 < len(markers) else len(text)
        sections[key] = text[start_pos:end_pos]

    return sections
