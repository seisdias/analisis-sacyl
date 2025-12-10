# -*- coding: utf-8 -*-
"""
Parsers de metadatos de análisis: fecha de finalización, nº de petición, origen.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Dict, Any, Optional


def parse_fecha_finalizacion(texto: str) -> str:
    """
    Busca la fecha de 'Finalización: dd/mm/aa' y la convierte a 'YYYY-MM-DD'.
    """
    m = re.search(r"Finalización:\s*([0-9]{1,2}/[0-9]{1,2}/[0-9]{2})", texto)
    if not m:
        raise ValueError("No se ha encontrado la fecha de Finalización en el PDF.")
    fecha_str = m.group(1)  # p.ej. '8/01/25'
    dt = datetime.strptime(fecha_str, "%d/%m/%y")
    return dt.strftime("%Y-%m-%d")


def parse_numero_peticion(texto: str) -> Optional[str]:
    """
    Extrae 'Nº petición: XXXXX'. Devuelve None si no lo encuentra.
    """
    m = re.search(r"Nº petición:\s*([0-9A-Za-z/]+)", texto)
    return m.group(1) if m else None


def parse_origen(texto: str) -> Optional[str]:
    """
    Extrae el campo 'Origen: ...'.
    """
    m = re.search(r"Origen:\s*(.+)", texto)
    if not m:
        return None
    linea = m.group(1)
    return linea.strip()


def parse_metadata(texto: str) -> Dict[str, Any]:
    """
    Devuelve un dict con los metadatos comunes del análisis:
      - fecha_analisis
      - numero_peticion
      - origen
    """
    fecha_analisis = parse_fecha_finalizacion(texto)
    numero_peticion = parse_numero_peticion(texto)
    origen = parse_origen(texto)

    return {
        "fecha_analisis": fecha_analisis,
        "numero_peticion": numero_peticion,
        "origen": origen,
    }
