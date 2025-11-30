# -*- coding: utf-8 -*-
"""
Conversor de informes PDF del HURH a JSON estructurado para análisis:

- Hematología
- Bioquímica
- Gasometría
- Orina
- Metadatos del paciente

Autor: Borja Alonso Tristán
Año: 2025
"""

import re
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from PyPDF2 import PdfReader


# ================================================================
#  UTILIDADES GENERALES
# ================================================================

def _extract_text_from_pdf(pdf_path: str) -> str:
    """Extrae todo el texto de un PDF como una única cadena."""
    reader = PdfReader(pdf_path)
    chunks = []
    for page in reader.pages:
        content = page.extract_text() or ""
        chunks.append(content)
    return "\n".join(chunks)


def _to_float(txt: Optional[str]) -> Optional[float]:
    if not txt:
        return None
    txt = txt.replace(",", ".")
    try:
        return float(txt)
    except ValueError:
        return None


def _extract_float(pattern: str, text: str) -> Optional[float]:
    """
    Busca un patrón que capture un número. Devuelve float o None.
    """
    m = re.search(pattern, text, flags=re.IGNORECASE)
    if not m:
        return None
    return _to_float(m.group(1))


def _extract_token(pattern: str, text: str) -> Optional[str]:
    m = re.search(pattern, text, flags=re.IGNORECASE)
    if not m:
        return None
    return m.group(1).strip()


# ================================================================
#  METADATOS DEL PDF
# ================================================================

def _parse_fecha(text: str) -> str:
    """
    Extrae 'Finalización: 07/10/25' y devuelve '2025-10-07'
    """
    m = re.search(r"Finalización:\s*([0-9]{1,2}/[0-9]{1,2}/[0-9]{2})", text)
    if not m:
        raise ValueError("No se ha encontrado la fecha de Finalización en el PDF.")
    raw = m.group(1)
    d = datetime.strptime(raw, "%d/%m/%y")
    return d.strftime("%Y-%m-%d")


def _parse_numero_peticion(text: str) -> Optional[str]:
    m = re.search(r"Nº petición:\s*([0-9A-Za-z]+)", text)
    return m.group(1) if m else None


def _parse_origen(text: str) -> Optional[str]:
    m = re.search(r"Origen:\s*(.+)", text)
    return m.group(1).strip() if m else None


# ================================================================
#  DATOS DEL PACIENTE
# ================================================================

PAT_NOMBRE = re.compile(r"Nombre:\s*(.*?)\s+Nº petición:", re.S)
PAT_APELLIDOS = re.compile(r"Apellidos:\s*(.*?)\s+Doctor:", re.S)
PAT_FECHA_SEXO = re.compile(r"Fecha nacimiento:\s*([\d/]+)\s+Sexo:\s*([MF])")
PAT_NHIST = re.compile(r"Nº Historia:\s*([^\n\r]+)")


def _clean_historia(raw: str) -> Optional[str]:
    """
    Solo acepta códigos tipo HURHxxxxx.
    """
    if not raw:
        return None
    token = raw.strip().split()[0]
    if re.match(r"^HURH[0-9A-Za-z]+$", token):
        return token
    return None


def _parse_patient(text: str) -> Dict[str, Any]:
    nombre = apellidos = fecha_nacimiento = sexo = numero_historia = None

    m = PAT_NOMBRE.search(text)
    if m:
        nombre = m.group(1).strip()

    m = PAT_APELLIDOS.search(text)
    if m:
        apellidos = m.group(1).strip()

    m = PAT_FECHA_SEXO.search(text)
    if m:
        raw_fecha = m.group(1).strip()
        sexo = m.group(2)
        try:
            d = datetime.strptime(raw_fecha, "%d/%m/%Y")
            fecha_nacimiento = d.strftime("%Y-%m-%d")
        except:
            fecha_nacimiento = raw_fecha

    m = PAT_NHIST.search(text)
    if m:
        numero_historia = _clean_historia(m.group(1))

    return {
        "nombre": nombre,
        "apellidos": apellidos,
        "fecha_nacimiento": fecha_nacimiento,
        "sexo": sexo,
        "numero_historia": numero_historia,
    }


# ================================================================
#  HEMATOLOGÍA
# ================================================================

def _parse_hematologia(text: str, fecha: str, num_pet: Optional[str]) -> Dict[str, Any]:
    out = {
        "fecha_analisis": fecha,
        "numero_peticion": num_pet,
    }

    def g(pattern): return _extract_float(pattern, text)

    # --- Serie blanca ---
    out["leucocitos"] = g(r"Leucocitos\s+\**([0-9]+[.,]?[0-9]*)")
    out["neutrofilos_pct"] = g(r"Neutrófilos\s*%\s+\**([0-9]+[.,]?[0-9]*)")
    out["linfocitos_pct"] = g(r"Linfocitos\s*%\s+\**([0-9]+[.,]?[0-9]*)")
    out["monocitos_pct"] = g(r"Monocitos\s*%\s+\**([0-9]+[.,]?[0-9]*)")
    out["eosinofilos_pct"] = g(r"Eosinófilos\s*%\s+\**([0-9]+[.,]?[0-9]*)")
    out["basofilos_pct"] = g(r"Basófilos\s*%\s+\**([0-9]+[.,]?[0-9]*)")

    out["neutrofilos_abs"] = g(r"Neutrófilos\s+\**([0-9]+[.,]?[0-9]*)\s*x10\^3")
    out["linfocitos_abs"] = g(r"Linfocitos\s+\**([0-9]+[.,]?[0-9]*)\s*x10\^3")
    out["monocitos_abs"] = g(r"Monocitos\s+\**([0-9]+[.,]?[0-9]*)\s*x10\^3")
    out["eosinofilos_abs"] = g(r"Eosinófilos\s+\**([0-9]+[.,]?[0-9]*)\s*x10\^3")
    out["basofilos_abs"] = g(r"Basófilos\s+\**([0-9]+[.,]?[0-9]*)\s*x10\^3")

    # --- Serie roja ---
    out["hematies"] = g(r"Hematíes\s+\**([0-9]+[.,]?[0-9]*)")
    out["hemoglobina"] = g(r"Hemoglobina\s+\**([0-9]+[.,]?[0-9]*)")
    out["hematocrito"] = g(r"Hematocrito\s+\**([0-9]+[.,]?[0-9]*)")
    out["vcm"] = g(r"V\.?C\.?M\.?\s+\**([0-9]+[.,]?[0-9]*)")
    out["hcm"] = g(r"H\.?C\.?M\.?\s+\**([0-9]+[.,]?[0-9]*)")
    out["chcm"] = g(r"C\.?H\.?C\.?M\.?\s+\**([0-9]+[.,]?[0-9]*)")
    out["rdw"] = g(r"R\.?D\.?W\.?\s+\**([0-9]+[.,]?[0-9]*)")

    # --- Serie plaquetas ---
    out["plaquetas"] = g(r"Plaquetas\s+\**([0-9]+[.,]?[0-9]*)")
    out["vpm"] = g(r"Volumen Plaquetar Medio\s+\**([0-9]+[.,]?[0-9]*)")

    return out


# ================================================================
#  BIOQUÍMICA
# ================================================================

def _parse_bioquimica(text: str, fecha: str, num_pet: Optional[str]) -> Optional[Dict[str, Any]]:
    out = {
        "fecha_analisis": fecha,
        "numero_peticion": num_pet,
    }

    def g(p): return _extract_float(p, text)

    out.update({
        "glucosa": g(r"Glucosa\s+\**([0-9]+[.,]?[0-9]*)"),
        "urea": g(r"Urea\s+\**([0-9]+[.,]?[0-9]*)"),
        "creatinina": g(r"Creatinina\s+\**([0-9]+[.,]?[0-9]*)"),
        "sodio": g(r"Sodio\s+\**([0-9]+[.,]?[0-9]*)"),
        "potasio": g(r"Potasio\s+\**([0-9]+[.,]?[0-9]*)"),
        "cloro": g(r"Cloro\s+\**([0-9]+[.,]?[0-9]*)"),
        "calcio": g(r"Calcio\s+\**([0-9]+[.,]?[0-9]*)"),
        "fosforo": g(r"Fósforo\s+\**([0-9]+[.,]?[0-9]*)"),
        "colesterol_total": g(r"Colesterol total\s+\**([0-9]+[.,]?[0-9]*)"),
        "colesterol_hdl": g(r"Colesterol HDL\s+\**([0-9]+[.,]?[0-9]*)"),
        "colesterol_ldl": g(r"Colesterol LDL\s+\**([0-9]+[.,]?[0-9]*)"),
        "colesterol_no_hdl": g(r"Colesterol no HDL\s+\**([0-9]+[.,]?[0-9]*)"),
        "trigliceridos": g(r"Triglicéridos\s+\**([0-9]+[.,]?[0-9]*)"),
        "indice_riesgo": g(r"Índice riesgo\s+\**([0-9]+[.,]?[0-9]*)"),
        "hierro": g(r"Hierro\s+\**([0-9]+[.,]?[0-9]*)"),
        "ferritina": g(r"Ferritina\s+\**([0-9]+[.,]?[0-9]*)"),
        "vitamina_b12": g(r"Vitamina\s+B12\s+\**([0-9]+[.,]?[0-9]*)"),
    })

    if any(v is not None for k, v in out.items() if k not in ("fecha_analisis", "numero_peticion")):
        return out
    return None


# ================================================================
#  GASOMETRÍA
# ================================================================

def _parse_gasometria(text: str, fecha: str, num_pet: Optional[str]) -> Optional[Dict[str, Any]]:
    out = {
        "fecha_analisis": fecha,
        "numero_peticion": num_pet,
    }

    def g(p): return _extract_float(p, text)
    def t(p): return _extract_token(p, text)

    out.update({
        "gaso_ph": g(r"\bpH\s+\**([0-9]+[.,]?[0-9]*)"),
        "gaso_pco2": g(r"pCO2\s+\**([0-9]+[.,]?[0-9]*)"),
        "gaso_po2": g(r"pO2\s+\**([0-9]+[.,]?[0-9]*)"),
        "gaso_tco2": g(r"CO2 Total.*?([0-9]+[.,]?[0-9]*)"),
        "gaso_so2_calc": t(r"Saturación de Oxígeno \(sO2\) calculada\s+([A-Za-z0-9.+-]+)"),
        "gaso_so2": t(r"Saturación de Oxígeno \(sO2\)\s+([A-Za-z0-9.+-]+)"),
        "gaso_p50": g(r"p50\s+\**([0-9]+[.,]?[0-9]*)"),
        "gaso_bicarbonato": g(r"Bicarbonato.*?\**([0-9]+[.,]?[0-9]*)"),
        "gaso_sbc": g(r"SBC\s+\**([0-9]+[.,]?[0-9]*)"),
        "gaso_eb": g(r"Exceso de Bases.*?\**([0-9]+[.,]?[0-9]*)"),
        "gaso_beecf": g(r"BEecf\s+\**([0-9]+[.,]?[0-9]*)"),
        "gaso_lactato": g(r"Lactato\s+\**([0-9]+[.,]?[0-9]*)"),
    })

    if any(v is not None for k, v in out.items() if k not in ("fecha_analisis", "numero_peticion")):
        return out
    return None


# ================================================================
#  ORINA
# ================================================================

def _parse_orina(text: str, fecha: str, num_pet: Optional[str]) -> Optional[Dict[str, Any]]:
    out = {
        "fecha_analisis": fecha,
        "numero_peticion": num_pet,
    }

    def g(p): return _extract_float(p, text)
    def t(p): return _extract_token(p, text)

    # Físico-químico
    out["orina_ph"] = g(r"\bpH\s+\**([0-9]+[.,]?[0-9]*)")
    out["orina_densidad"] = g(r"Densidad\s+\**([0-9]+[.,]?[0-9]*)")

    # Tiras
    out["proteinas"] = t(r"Prote[ií]nas\s+\**([A-Za-z+]+)")
    out["glucosa_orina"] = t(r"Glucosa\s+\**([A-Za-z+]+)")
    out["sangre"] = t(r"Sangre\s+\**([A-Za-z+]+)")
    out["nitritos"] = t(r"Nitritos\s+\**([A-Za-z+]+)")
    out["leucocitos_ests"] = t(r"Leucocitos esterasas?\s+\**([A-Za-z+]+)")
    out["bilirrubina"] = t(r"Bilirrubina\s+\**([A-Za-z+]+)")
    out["urobilinogeno"] = t(r"Urobilin[oó]geno\s+\**([A-Za-z+]+)")

    # Cuantitativos
    out["sodio_ur"] = g(r"Sodio.*?orina.*?\**([0-9]+[.,]?[0-9]*)")
    out["creatinina_ur"] = g(r"Creatinina.*?orina.*?\**([0-9]+[.,]?[0-9]*)")
    out["indice_albumina_creatinina"] = g(r"Índice\s+Alb/Cre\s+\**([0-9]+[.,]?[0-9]*)")
    out["albumina_ur"] = g(r"Albúmina.*?orina.*?\**([0-9]+[.,]?[0-9]*)")

    if any(v is not None for k, v in out.items() if k not in ("fecha_analisis", "numero_peticion")):
        return out
    return None


# ================================================================
#  PARSE PDF COMPLETO
# ================================================================

def parse_hematology_pdf(pdf_path: str) -> Dict[str, Any]:
    text = _extract_text_from_pdf(pdf_path)

    paciente = _parse_patient(text)
    fecha = _parse_fecha(text)
    num_pet = _parse_numero_peticion(text)
    origen = _parse_origen(text)

    hema = _parse_hematologia(text, fecha, num_pet)
    hema["origen"] = origen

    bio = _parse_bioquimica(text, fecha, num_pet)
    gas = _parse_gasometria(text, fecha, num_pet)
    ori = _parse_orina(text, fecha, num_pet)

    out = {
        "paciente": paciente,
        "analisis": [hema],        # compatibilidad
        "hematologia": [hema],
    }

    if bio:
        out["bioquimica"] = [bio]
    if gas:
        out["gasometria"] = [gas]
    if ori:
        out["orina"] = [ori]

    return out


# ================================================================
#  CLI
# ================================================================

def pdf_to_json_file(pdf_path: str, json_path: str) -> None:
    data = parse_hematology_pdf(pdf_path)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Uso: python pdf_to_json.py <informe.pdf> [salida.json]")
        exit()

    pdf_in = sys.argv[1]
    if len(sys.argv) >= 3:
        json_out = sys.argv[2]
    else:
        json_out = str(Path(pdf_in).with_suffix(".json"))

    pdf_to_json_file(pdf_in, json_out)
    print(f"JSON generado: {json_out}")