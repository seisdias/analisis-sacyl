# -*- coding: utf-8 -*-
"""
Conversor de informes PDF de laboratorio a JSON de análisis de hematología,
bioquímica, gasometría y orina.

Autor: Borja Alonso Tristán
Año: 2025
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any

from .pdf_utils import extract_text_from_pdf, has_any_value
from .metadata_parser import parse_metadata
from .patient_parser import parse_patient
from .section_splitter import split_lab_sections
from .hematologia_parser import parse_hematologia_section
from .bioquimica_parser import parse_bioquimica_section
from .gasometria_parser import parse_gasometria_section
from .orina_parser import parse_orina_section


# ============================================================
#   FUNCIÓN PRINCIPAL (API PÚBLICA)
# ============================================================

def parse_hematology_pdf(pdf_path: str) -> Dict[str, Any]:
    """
    Parsea un informe PDF de laboratorio y devuelve un dict con formato:

    {
      "paciente": {...},
      "hematologia": [ {...} ],
      "bioquimica":  [ {...} ],
      "gasometria":  [ {...} ],
      "orina":       [ {...} ],
      "analisis":    [ {...} ]  # alias de hematologia para compatibilidad
    }

    (Si alguna serie no está presente, vendrá como lista vacía o no se incluirá.)
    """
    pdf_path = str(pdf_path)
    texto = extract_text_from_pdf(pdf_path)

    # --- Datos de paciente ---
    paciente_data = parse_patient(texto)

    # --- Metadatos comunes ---
    meta = parse_metadata(texto)
    fecha_analisis = meta["fecha_analisis"]
    numero_peticion = meta["numero_peticion"]
    origen = meta["origen"]

    # --- Secciones del informe ---
    sections = split_lab_sections(texto)

    hemat_text = sections.get("hematologia", texto)
    bio_text = sections.get("bioquimica", texto)
    gaso_text = sections.get("gasometria", texto)
    orina_text = sections.get("orina", "")

    # --- Hematología ---
    hemat_vals = parse_hematologia_section(hemat_text)
    has_hema = has_any_value(hemat_vals)

    # --- Bioquímica ---
    bio_vals = parse_bioquimica_section(bio_text) if "bioquimica" in sections else {}
    has_bio = has_any_value(bio_vals)

    # --- Gasometría ---
    gaso_vals = parse_gasometria_section(gaso_text) if "gasometria" in sections else {}
    has_gaso = has_any_value(gaso_vals)

    # --- Orina ---
    orina_vals = parse_orina_section(orina_text) if "orina" in sections else {}
    has_orina = has_any_value(orina_vals)

    # Si no hay ningún bloque reconocible, probablemente no es un informe de lab estándar
    if not (has_hema or has_bio or has_gaso or has_orina):
        raise ValueError(
            "El PDF no parece ser un informe de laboratorio (hemograma/bioquímica/"
            "gasometría/orina) reconocible y no se importará."
        )

    result: Dict[str, Any] = {
        "paciente": paciente_data or {},
    }

    if has_hema:
        hemat_record = {
            "fecha_analisis": fecha_analisis,
            "numero_peticion": numero_peticion,
            "origen": origen,
            **hemat_vals,
        }
        result["hematologia"] = [hemat_record]

    if has_bio:
        bio_record = {
            "fecha_analisis": fecha_analisis,
            "numero_peticion": numero_peticion,
            **bio_vals,
        }
        result["bioquimica"] = [bio_record]

    if has_gaso:
        gaso_record = {
            "fecha_analisis": fecha_analisis,
            "numero_peticion": numero_peticion,
            **gaso_vals,
        }
        result["gasometria"] = [gaso_record]

    if has_orina:
        orina_record = {
            "fecha_analisis": fecha_analisis,
            "numero_peticion": numero_peticion,
            **orina_vals,
        }
        result["orina"] = [orina_record]

    return result


# ============================================================
#   UTILIDAD LÍNEA DE COMANDOS
# ============================================================

def pdf_to_json_file(pdf_path: str, json_path: str) -> None:
    """
    Convierte un PDF a JSON y lo guarda en 'json_path'.
    """
    data = parse_hematology_pdf(pdf_path)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Uso: python pdf_to_json.py <informe.pdf> [salida.json]")
        sys.exit(1)

    pdf_in = sys.argv[1]
    if len(sys.argv) >= 3:
        json_out = sys.argv[2]
    else:
        # Por defecto, mismo nombre con extensión .json
        p = Path(pdf_in)
        json_out = str(p.with_suffix(".json"))

    pdf_to_json_file(pdf_in, json_out)
    print(f"JSON generado: {json_out}")
