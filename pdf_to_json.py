# -*- coding: utf-8 -*-
"""
Conversor de informes PDF de laboratorio a JSON de análisis de hematología.
Autor: Borja Alonso Tristán
Año: 2025
"""

import re
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from PyPDF2 import PdfReader


def _extract_text_from_pdf(pdf_path: str) -> str:
    """Extrae todo el texto de un PDF en una sola cadena."""
    reader = PdfReader(pdf_path)
    chunks = []
    for page in reader.pages:
        txt = page.extract_text() or ""
        chunks.append(txt)
    return "\n".join(chunks)


def _parse_fecha_finalizacion(texto: str) -> str:
    """
    Busca la fecha de 'Finalización: dd/mm/aa' y la convierte a 'YYYY-MM-DD'.
    """
    m = re.search(r"Finalización:\s*([0-9]{1,2}/[0-9]{1,2}/[0-9]{2})", texto)
    if not m:
        raise ValueError("No se ha encontrado la fecha de Finalización en el PDF.")
    fecha_str = m.group(1)  # p.ej. '8/01/25'
    dt = datetime.strptime(fecha_str, "%d/%m/%y")
    return dt.strftime("%Y-%m-%d")


def _parse_numero_peticion(texto: str) -> str:
    """
    Extrae el 'Nº petición: XXXXX'. Devuelve None si no lo encuentra.
    """
    m = re.search(r"Nº petición:\s*([0-9A-Za-z]+)", texto)
    return m.group(1) if m else None


def _parse_origen(texto: str) -> str:
    """
    Extrae el campo 'Origen: ...' en la parte del informe.
    """
    m = re.search(r"Origen:\s*(.+)", texto)
    if not m:
        return None
    # Solo la primera línea tras 'Origen:'
    linea = m.group(1)
    return linea.strip()


def _extract_float(pattern: str, texto: str) -> float:
    """
    Aplica un patrón regex y devuelve el primer grupo capturado como float.
    Si no encuentra nada, devuelve None.
    """
    m = re.search(pattern, texto)
    if not m:
        return None
    valor_str = m.group(1).replace(",", ".")
    try:
        return float(valor_str)
    except ValueError:
        return None


# -------------------------------
#  Patrones y parser de paciente
# -------------------------------

PAT_NOMBRE = re.compile(r"Nombre:\s*(.*?)\s+Nº petición:", re.S)
PAT_APELLIDOS = re.compile(r"Apellidos:\s*(.*?)\s+Doctor:", re.S)
PAT_FECHA_SEXO = re.compile(r"Fecha nacimiento:\s*([\d/]+)\s+Sexo:\s*([MF])")
PAT_NHIST = re.compile(r"Nº Historia:\s*([^\n\r]+)")


def _parse_patient(text: str) -> dict:
    """
    Extrae los datos básicos del paciente a partir del texto completo del PDF.

    Devuelve un dict con:
      - nombre
      - apellidos
      - fecha_nacimiento (ISO YYYY-MM-DD si se puede)
      - sexo
      - numero_historia
    """
    nombre = apellidos = fecha_nacimiento = sexo = numero_historia = None

    m = PAT_NOMBRE.search(text)
    if m:
        nombre = m.group(1).strip()

    m = PAT_APELLIDOS.search(text)
    if m:
        apellidos = m.group(1).strip()

    m = PAT_FECHA_SEXO.search(text)
    if m:
        raw_fecha = m.group(1).strip()  # p.ej. '23/06/1980'
        sexo = m.group(2).strip()
        try:
            dt = datetime.strptime(raw_fecha, "%d/%m/%Y")
            fecha_nacimiento = dt.strftime("%Y-%m-%d")
        except ValueError:
            # Si falla, dejamos el formato original
            fecha_nacimiento = raw_fecha

    m = PAT_NHIST.search(text)
    if m:
        numero_historia = m.group(1).strip()
        # En algunos informes viene "HURH298152 Hematología"
        # -> nos quedamos con la primera palabra
        numero_historia = numero_historia.split()[0]

    return {
        "nombre": nombre,
        "apellidos": apellidos,
        "fecha_nacimiento": fecha_nacimiento,
        "sexo": sexo,
        "numero_historia": numero_historia,
    }


def parse_hematology_pdf(pdf_path: str) -> Dict[str, Any]:
    """
    Parsea un informe PDF de laboratorio y devuelve un dict con el formato:

    {
      "paciente": { ... },
      "analisis": [
        { ... }
      ]
    }

    Listo para pasarlo a HematologyDB.import_from_json().
    """
    pdf_path = str(pdf_path)
    texto = _extract_text_from_pdf(pdf_path)

    # --- Datos de paciente ---
    paciente = _parse_patient(texto)

    # --- Metadatos del análisis ---
    fecha_analisis = _parse_fecha_finalizacion(texto)
    numero_peticion = _parse_numero_peticion(texto)
    origen = _parse_origen(texto)

    # --- Serie blanca ---
    leucocitos = _extract_float(r"Leucocitos\s+\**([0-9]+(?:[.,][0-9]+)?)\s+x10\^3/µL", texto)

    neutrofilos_pct = _extract_float(r"Neutrófilos %\s+\**([0-9]+(?:[.,][0-9]+)?)\s+%", texto)
    linfocitos_pct = _extract_float(r"Linfocitos %\s+\**([0-9]+(?:[.,][0-9]+)?)\s+%", texto)
    monocitos_pct = _extract_float(r"Monocitos %\s+\**([0-9]+(?:[.,][0-9]+)?)\s+%", texto)
    eosinofilos_pct = _extract_float(r"Eosinófilos %\s+\**([0-9]+(?:[.,][0-9]+)?)\s+%", texto)
    basofilos_pct = _extract_float(r"Basófilos %\s+\**([0-9]+(?:[.,][0-9]+)?)\s+%", texto)

    neutrofilos_abs = _extract_float(
        r"Neutrófilos\s+\**([0-9]+(?:[.,][0-9]+)?)\s+x10\^3/µL", texto
    )
    linfocitos_abs = _extract_float(
        r"Linfocitos\s+\**([0-9]+(?:[.,][0-9]+)?)\s+x10\^3/µL", texto
    )
    monocitos_abs = _extract_float(
        r"Monocitos\s+\**([0-9]+(?:[.,][0-9]+)?)\s+x10\^3/µL", texto
    )
    eosinofilos_abs = _extract_float(
        r"Eosinófilos\s+\**([0-9]+(?:[.,][0-9]+)?)\s+x10\^3/µL", texto
    )
    basofilos_abs = _extract_float(
        r"Basófilos\s+\**([0-9]+(?:[.,][0-9]+)?)\s+x10\^3/µL", texto
    )

    # --- Serie roja ---
    hematies = _extract_float(r"Hematíes\s+\**([0-9]+(?:[.,][0-9]+)?)\s+x10\^6/µL", texto)
    hemoglobina = _extract_float(r"Hemoglobina\s+\**([0-9]+(?:[.,][0-9]+)?)\s+g/dL", texto)
    hematocrito = _extract_float(r"Hematocrito\s+\**([0-9]+(?:[.,][0-9]+)?)\s+%", texto)
    vcm = _extract_float(r"V\.C\.M\s+\**([0-9]+(?:[.,][0-9]+)?)\s+fL", texto)
    hcm = _extract_float(r"H\.C\.M\.\s+\**([0-9]+(?:[.,][0-9]+)?)\s+pg", texto)
    chcm = _extract_float(r"C\.H\.C\.M\.\s+\**([0-9]+(?:[.,][0-9]+)?)\s+g/dL", texto)
    rdw = _extract_float(r"R\.D\.W\s+\**([0-9]+(?:[.,][0-9]+)?)\s+%", texto)

    # --- Serie plaquetar ---
    plaquetas = _extract_float(r"Plaquetas\s+\**([0-9]+(?:[.,][0-9]+)?)\s+x10\^3/µL", texto)
    vpm = _extract_float(
        r"Volumen Plaquetar Medio\s+\**([0-9]+(?:[.,][0-9]+)?)\s+fL", texto
    )

    analisis = {
        "fecha_analisis": fecha_analisis,
        "numero_peticion": numero_peticion,
        "origen": origen,

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

    # Estructura final: paciente + lista de análisis
    return {
        "paciente": paciente,
        "analisis": [analisis],
    }


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
