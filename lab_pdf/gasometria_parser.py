# -*- coding: utf-8 -*-
"""
Parser específico de la sección de GASOMETRÍA.
"""

from __future__ import annotations

from typing import Dict, Optional

from .pdf_utils import extract_named_value


def parse_gasometria_section(texto: str) -> Dict[str, Optional[float]]:
    """
    Parsea la sección de GASOMETRÍA (venosa/arterial) y devuelve un dict.
    """
    data: Dict[str, Optional[float]] = {}

    data["gaso_ph"] = extract_named_value("pH", texto)
    data["gaso_pco2"] = extract_named_value("pCO2", texto)
    data["gaso_po2"] = extract_named_value("pO2", texto)
    data["gaso_tco2"] = extract_named_value("CO2 Total (TCO2)", texto)

    data["gaso_so2_calc"] = extract_named_value(
        "Saturación de Oxígeno (sO2) calculada", texto
    )
    data["gaso_so2"] = extract_named_value(
        "Saturación de Oxígeno (sO2)", texto
    )

    data["gaso_p50"] = extract_named_value("p50", texto)
    data["gaso_bicarbonato"] = extract_named_value("Bicarbonato (CO3H-)", texto)
    data["gaso_sbc"] = extract_named_value("Bicarbonato Estandar (SBC)", texto)
    data["gaso_eb"] = extract_named_value("Exceso de Bases (EB)", texto)
    data["gaso_beecf"] = extract_named_value(
        "E. de bases en fluido extracelular (BEecf)", texto
    )
    data["gaso_calcio_ionico"] = extract_named_value("Calcio iónico", texto)
    data["gaso_lactato"] = extract_named_value("Lactato", texto)

    return data
