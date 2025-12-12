# -*- coding: utf-8 -*-
"""
Parser específico de la sección de HEMATOLOGÍA (hemograma).
Robusto frente a asteriscos (*) y espaciado irregular típico de PDFs.
"""

from __future__ import annotations

import re
from typing import Dict, Optional

from .pdf_utils import extract_float


_NUM = r"([0-9]+(?:[.,][0-9]+)?)"


def _normalize_text(texto: str) -> str:
    """
    Normaliza el texto extraído de PDF para facilitar regex:
    - unifica espacios (incluye NBSP)
    - separa asteriscos pegados a valores (3.6* -> 3.6 *)
    - colapsa múltiples espacios/saltos
    """
    if not texto:
        return ""

    t = texto.replace("\u00A0", " ")  # NBSP -> espacio normal
    # Asegura que '*' esté separado
    t = t.replace("*", " * ")
    # Colapsa espacios
    t = re.sub(r"[ \t]+", " ", t)
    # Normaliza saltos a '\n' y colapsa líneas muy fragmentadas
    t = t.replace("\r\n", "\n").replace("\r", "\n")
    t = re.sub(r"\n{2,}", "\n", t)
    return t


def parse_hematologia_section(texto: str) -> Dict[str, Optional[float]]:
    """
    Extrae datos de hemograma / hematología básica a partir SOLO del texto
    de la sección de hematología.
    """
    texto = _normalize_text(texto)

    # Helpers para unidades frecuentes (con tolerancia a espacios)
    u_x10_3 = r"x\s*10\s*\^\s*3\s*/\s*µL"
    u_x10_6 = r"x\s*10\s*\^\s*6\s*/\s*µL"

    # ------------------------------------------------------------
    # Serie blanca
    # ------------------------------------------------------------
    leucocitos = extract_float(
        rf"Leucocitos\s*\*?\s*{_NUM}\s*{u_x10_3}",
        texto
    )

    neutrofilos_pct = extract_float(
        rf"Neutrófilos\s*%\s*\*?\s*{_NUM}\s*%",
        texto
    )
    linfocitos_pct = extract_float(
        rf"Linfocitos\s*%\s*\*?\s*{_NUM}\s*%",
        texto
    )
    monocitos_pct = extract_float(
        rf"Monocitos\s*%\s*\*?\s*{_NUM}\s*%",
        texto
    )
    eosinofilos_pct = extract_float(
        rf"Eosinófilos\s*%\s*\*?\s*{_NUM}\s*%",
        texto
    )
    basofilos_pct = extract_float(
        rf"Basófilos\s*%\s*\*?\s*{_NUM}\s*%",
        texto
    )

    neutrofilos_abs = extract_float(
        rf"Neutrófilos(?!\s*%)\s*\*?\s*{_NUM}\s*{u_x10_3}",
        texto
    )
    linfocitos_abs = extract_float(
        rf"Linfocitos(?!\s*%)\s*\*?\s*{_NUM}\s*{u_x10_3}",
        texto
    )
    monocitos_abs = extract_float(
        rf"Monocitos(?!\s*%)\s*\*?\s*{_NUM}\s*{u_x10_3}",
        texto
    )
    eosinofilos_abs = extract_float(
        rf"Eosinófilos(?!\s*%)\s*\*?\s*{_NUM}\s*{u_x10_3}",
        texto
    )
    basofilos_abs = extract_float(
        rf"Basófilos(?!\s*%)\s*\*?\s*{_NUM}\s*{u_x10_3}",
        texto
    )

    # ------------------------------------------------------------
    # Serie roja
    # ------------------------------------------------------------
    hematies = extract_float(
        rf"Hematíes\s*\*?\s*{_NUM}\s*{u_x10_6}",
        texto
    )
    hemoglobina = extract_float(
        rf"Hemoglobina\s*\*?\s*{_NUM}\s*g\s*/\s*dL",
        texto
    )
    hematocrito = extract_float(
        rf"Hematocrito\s*\*?\s*{_NUM}\s*%",
        texto
    )

    # Muchos PDFs parten V.C.M / H.C.M / C.H.C.M / R.D.W con puntos y espacios raros
    vcm = extract_float(
        rf"V\s*\.?\s*C\s*\.?\s*M\s*\*?\s*{_NUM}\s*fL",
        texto
    )
    hcm = extract_float(
        rf"H\s*\.?\s*C\s*\.?\s*M\s*\.?\s*\*?\s*{_NUM}\s*pg",
        texto
    )
    chcm = extract_float(
        rf"C\s*\.?\s*H\s*\.?\s*C\s*\.?\s*M\s*\.?\s*\*?\s*{_NUM}\s*g\s*/\s*dL",
        texto
    )
    rdw = extract_float(
        rf"R\s*\.?\s*D\s*\.?\s*W\s*\*?\s*{_NUM}\s*%",
        texto
    )

    # ------------------------------------------------------------
    # Serie plaquetar
    # ------------------------------------------------------------
    plaquetas = extract_float(
        rf"Plaquetas\s*\*?\s*{_NUM}\s*{u_x10_3}",
        texto
    )

    # Este campo a veces aparece como "Volumen plaquetar medio", "VPM", etc.
    vpm = extract_float(
        rf"(?:Volumen\s*Plaquetar\s*Medio|VPM)\s*\*?\s*{_NUM}\s*fL",
        texto
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
