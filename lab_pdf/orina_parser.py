# -*- coding: utf-8 -*-
"""
Parser específico de la sección de ORINA / urinoanálisis.
"""

from __future__ import annotations

from typing import Dict, Any

from .pdf_utils import extract_float, extract_token


def parse_orina_section(texto: str) -> Dict[str, Any]:
    """
    Extrae parámetros de orina / urinoanálisis a partir del texto
    de la sección de ORINA (si existe).
    """
    data: Dict[str, Any] = {}

    # Físico-químico
    data["ph"] = extract_float(r"\bpH\s+\**([0-9]+(?:[.,][0-9]+)?)\s*", texto)
    data["densidad"] = extract_float(r"Densidad\s+\**([0-9]+(?:[.,][0-9]+)?)\s*", texto)

    # Tiras / cualitativos
    data["glucosa"] = extract_token(r"Glucosa\s+\**([A-Za-z+]+)", texto)
    data["proteinas"] = extract_token(r"Proteínas\s+\**([A-Za-z+]+)", texto)
    data["cuerpos_cetonicos"] = extract_token(
        r"Cuerpos cetónicos\s+\**([A-Za-z+]+)", texto
    )
    data["sangre"] = extract_token(r"Sangre\s+\**([A-Za-z+]+)", texto)
    data["nitritos"] = extract_token(r"Nitritos\s+\**([A-Za-z+]+)", texto)
    data["leucocitos_ests"] = extract_token(
        r"Leucocitos esterasas?\s+\**([A-Za-z+]+)", texto
    )
    data["bilirrubina"] = extract_token(r"Bilirrubina\s+\**([A-Za-z+]+)", texto)
    data["urobilinogeno"] = extract_token(
        r"Urobilinógeno\s+\**([A-Za-z+]+)", texto
    )

    # Cuantitativos de orina (si los hubiera)
    data["sodio_ur"] = extract_float(
        r"Sodio\s+orina\s+\**([0-9]+(?:[.,][0-9]+)?)\s+", texto
    )
    data["creatinina_ur"] = extract_float(
        r"Creatinina\s+orina\s+\**([0-9]+(?:[.,][0-9]+)?)\s+", texto
    )
    data["indice_albumina_creatinina"] = extract_float(
        r"Índice\s+Alb/Cre\s+\**([0-9]+(?:[.,][0-9]+)?)\s+", texto
    )
    data["albumina_ur"] = extract_float(
        r"Albúmina\s+orina\s+\**([0-9]+(?:[.,][0-9]+)?)\s+", texto
    )
    data["categoria_albuminuria"] = extract_token(
        r"Categoría\s+albuminuria\s+\**([A-Za-z0-9 ]+)", texto
    )

    return data
