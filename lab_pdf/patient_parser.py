# -*- coding: utf-8 -*-
"""
Parser de datos de paciente a partir del texto completo del informe.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Dict, Any, Optional


PAT_NOMBRE = re.compile(r"Nombre:\s*(.*?)\s+Nº petición:", re.S)
PAT_APELLIDOS = re.compile(r"Apellidos:\s*(.*?)\s+Doctor:", re.S)
PAT_FECHA_SEXO_ORIGEN = re.compile(r"Fecha nacimiento:\s*([\d/]+)\s+Sexo:\s*([MF])\s+Origen:\s*(.*?)")
PAT_NHIST = re.compile(r"Nº Historia:\s*([^\n\r]+)")


def _clean_historia(raw: str) -> Optional[str]:
    """
    Normaliza y filtra el nº de historia clínico.

    Reglas:
      - Nos quedamos con la primera palabra de la línea.
      - Solo aceptamos valores que empiecen por 'HURH'.
      - Si no cumple el formato -> devolvemos None.
    """
    if not raw:
        return None
    first = raw.strip().split()[0]
    first = first.strip()
    if not first:
        return None

    # Solo aceptamos HURHxxxxx (letras/números detrás)
    if re.match(r"^HURH[0-9A-Za-z]+$", first):
        return first
    return None


def parse_patient(text: str) -> Dict[str, Any]:
    """
    Extrae los datos básicos del paciente:

      - nombre
      - apellidos
      - fecha_nacimiento (ISO YYYY-MM-DD si se puede)
      - sexo
      - numero_historia (solo si cumple patrón HURH...)
    """
    nombre = apellidos = fecha_nacimiento = sexo = numero_historia = origen = None

    m = PAT_NOMBRE.search(text)
    if m:
        nombre = m.group(1).strip()

    m = PAT_APELLIDOS.search(text)
    if m:
        apellidos = m.group(1).strip()

    m = PAT_FECHA_SEXO_ORIGEN.search(text)
    if m:
        raw_fecha = m.group(1).strip()  # p.ej. '23/06/1980'
        sexo = m.group(2).strip()
        origen = m.group(3).strip()
        try:
            dt = datetime.strptime(raw_fecha, "%d/%m/%Y")
            fecha_nacimiento = dt.strftime("%Y-%m-%d")
        except ValueError:
            fecha_nacimiento = raw_fecha

    m = PAT_NHIST.search(text)
    if m:
        raw_hist = m.group(1).strip()
        numero_historia = _clean_historia(raw_hist)

    return {
        "nombre": nombre,
        "apellidos": apellidos,
        "fecha_nacimiento": fecha_nacimiento,
        "sexo": sexo,
        "numero_historia": numero_historia,
        "origen": origen
    }
