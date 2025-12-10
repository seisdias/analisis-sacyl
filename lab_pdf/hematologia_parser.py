# -*- coding: utf-8 -*-
"""
Parser específico de la sección de HEMATOLOGÍA (hemograma).
"""

from __future__ import annotations

from typing import Dict, Optional
from .pdf_utils import extract_float


def parse_hematologia_section(texto: str) -> Dict[str, Optional[float]]:
    """
    Extrae los datos de hemograma / hematología básica a partir
    SOLO del texto de la sección de hematología.
    """
    # --- Serie blanca ---
    leucocitos = extract_float(
        r"Leucocitos\s+\**([0-9]+(?:[.,][0-9]+)?)\s+x10\^3/µL", texto
    )

    neutrofilos_pct = extract_float(
        r"Neutrófilos %\s+\**([0-9]+(?:[.,][0-9]+)?)\s+%", texto
    )
    linfocitos_pct = extract_float(
        r"Linfocitos %\s+\**([0-9]+(?:[.,][0-9]+)?)\s+%", texto
    )
    monocitos_pct = extract_float(
        r"Monocitos %\s+\**([0-9]+(?:[.,][0-9]+)?)\s+%", texto
    )
    eosinofilos_pct = extract_float(
        r"Eosinófilos %\s+\**([0-9]+(?:[.,][0-9]+)?)\s+%", texto
    )
    basofilos_pct = extract_float(
        r"Basófilos %\s+\**([0-9]+(?:[.,][0-9]+)?)\s+%", texto
    )

    neutrofilos_abs = extract_float(
        r"Neutrófilos\s+\**([0-9]+(?:[.,][0-9]+)?)\s+x10\^3/µL", texto
    )
    linfocitos_abs = extract_float(
        r"Linfocitos\s+\**([0-9]+(?:[.,][0-9]+)?)\s+x10\^3/µL", texto
    )
    monocitos_abs = extract_float(
        r"Monocitos\s+\**([0-9]+(?:[.,][0-9]+)?)\s+x10\^3/µL", texto
    )
    eosinofilos_abs = extract_float(
        r"Eosinófilos\s+\**([0-9]+(?:[.,][0-9]+)?)\s+x10\^3/µL", texto
    )
    basofilos_abs = extract_float(
        r"Basófilos\s+\**([0-9]+(?:[.,][0-9]+)?)\s+x10\^3/µL", texto
    )

    # --- Serie roja ---
    hematies = extract_float(
        r"Hematíes\s+\**([0-9]+(?:[.,][0-9]+)?)\s+x10\^6/µL", texto
    )
    hemoglobina = extract_float(
        r"Hemoglobina\s+\**([0-9]+(?:[.,][0-9]+)?)\s+g/dL", texto
    )
    hematocrito = extract_float(
        r"Hematocrito\s+\**([0-9]+(?:[.,][0-9]+)?)\s+%", texto
    )
    vcm = extract_float(
        r"V\.C\.M\s+\**([0-9]+(?:[.,][0-9]+)?)\s+fL", texto
    )
    hcm = extract_float(
        r"H\.C\.M\.\s+\**([0-9]+(?:[.,][0-9]+)?)\s+pg", texto
    )
    chcm = extract_float(
        r"C\.H\.C\.M\.\s+\**([0-9]+(?:[.,][0-9]+)?)\s+g/dL", texto
    )
    rdw = extract_float(
        r"R\.D\.W\s+\**([0-9]+(?:[.,][0-9]+)?)\s+%", texto
    )

    # --- Serie plaquetar ---
    plaquetas = extract_float(
        r"Plaquetas\s+\**([0-9]+(?:[.,][0-9]+)?)\s+x10\^3/µL", texto
    )
    vpm = extract_float(
        r"Volumen Plaquetar Medio\s+\**([0-9]+(?:[.,][0-9]+)?)\s+fL", texto
    )

    return {
        "leucocitos": leucocitos,
        "neutrofilos_pct": neutrofilos_pct,
        "linfocitos_pct": linfocitos_pct,
        "monocitos_pct": monocitos_pct,
        "eosinofilos_pct": eosinofilos_pct,
        "basofilos_pct": basofilos_pct,

        "neutrofilos_abs": neutrofilos_abs,
        "linfocitos_abs": linfocitos_abs,
        "monocitos_abs": monocitos_abs,
        "eosinofilos_abs": eosinofilos_abs,
        "basofilos_abs": basofilos_abs,

        "hematies": hematies,
        "hemoglobina": hemoglobina,
        "hematocrito": hematocrito,
        "vcm": vcm,
        "hcm": hcm,
        "chcm": chcm,
        "rdw": rdw,

        "plaquetas": plaquetas,
        "vpm": vpm,
    }
