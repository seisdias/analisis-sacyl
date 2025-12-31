# -*- coding: utf-8 -*-
"""
Escáner de parámetros de laboratorio en PDFs HURH.

- Recorre todos los PDFs de un directorio.
- Extrae líneas de resultados tipo:
    Nombre     valor   unidad   rango_min - rango_max
- Construye un diccionario con:
    - nombre normalizado
    - nombres originales
    - unidades observadas
    - rangos (mín, máx) observados

Uso:
    python3.14 scan_lab_params.py ruta_directorio_pdfs salida.json

Ejemplo:
    python3.14 scan_lab_params.py ./pdfs_analisis parametros_laboratorio.json
"""

import sys
import os
import re
import json
from typing import Dict, Any, Tuple, Optional, List

from PyPDF2 import PdfReader


def extract_text_from_pdf(path: str) -> str:
    reader = PdfReader(path)
    chunks = []
    for page in reader.pages:
        txt = page.extract_text() or ""
        chunks.append(txt)
    return "\n".join(chunks)


def normalize_name(name: str) -> str:
    """
    Normaliza el nombre del parámetro para agrupar:
    - strip
    - colapsar espacios
    - pasar a mayúsculas
    """
    name = (name or "").strip()
    name = " ".join(name.split())
    return name.upper()


def parse_numeric_line(line: str) -> Optional[Tuple[str, float, str, float, float]]:
    """
    Intenta parsear una línea de resultado numérico con rango de referencia.

    Ejemplos que queremos captar:

        Glucosa             92 mg/dL        70 - 110
        Cloruro            102 mmol/L       98 - 107
        Hemoglobina        14,1 g/dL     13,5 - 17,5

    Devuelve:
        (nombre, valor, unidad, ref_min, ref_max)
    o None si no encaja.
    """
    # Permitimos letras, acentos, %, paréntesis, etc. en el nombre
    pattern = (
        r"""^
        (?P<name>[A-Za-zÁÉÍÓÚÜáéíóúÑñçÇ0-9 %()\/\.\-]+?)   # nombre
        \s+\**                                             # espacios y posibles asteriscos
        (?P<value>[0-9]+(?:[.,][0-9]+)?)                   # valor
        \s+
        (?P<unit>[\w\/%\.\u00B5µ·]+)                       # unidad (mg/dL, mmol/L, %, µmol/L, etc.)
        \s+
        (?P<ref_min>[0-9]+(?:[.,][0-9]+)?)                 # rango mínimo
        \s*[-–]\s*                                         # guion (puede ser - o –)
        (?P<ref_max>[0-9]+(?:[.,][0-9]+)?)                 # rango máximo
        """
    )

    m = re.match(pattern, line, flags=re.VERBOSE)
    if not m:
        return None

    name = m.group("name").strip()
    value = float(m.group("value").replace(",", "."))
    unit = m.group("unit").strip()
    ref_min = float(m.group("ref_min").replace(",", "."))
    ref_max = float(m.group("ref_max").replace(",", "."))

    return name, value, unit, ref_min, ref_max


def scan_directory(dir_path: str) -> Dict[str, Any]:
    """
    Recorre todos los PDFs de dir_path, extrae parámetros y construye
    un diccionario agregado.
    """
    params: Dict[str, Dict[str, Any]] = {}

    pdf_files: List[str] = [
        os.path.join(dir_path, f)
        for f in os.listdir(dir_path)
        if f.lower().endswith(".pdf")
    ]

    pdf_files.sort()

    if not pdf_files:
        print(f"[AVISO] No se han encontrado PDFs en {dir_path}")
        return params

    for pdf_path in pdf_files:
        print(f"[INFO] Procesando: {os.path.basename(pdf_path)}")
        try:
            text = extract_text_from_pdf(pdf_path)
        except Exception as e:
            print(f"  [ERROR] No se pudo leer el PDF: {e}")
            continue

        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            parsed = parse_numeric_line(line)
            if not parsed:
                continue

            name_orig, value, unit, ref_min, ref_max = parsed
            key = normalize_name(name_orig)

            if key not in params:
                params[key] = {
                    "normalized_key": key,
                    "original_names": set(),
                    "units": set(),
                    "ranges": set(),   # se guardan como tuplas (min, max)
                    "examples": []
                }

            entry = params[key]
            entry["original_names"].add(name_orig.strip())
            entry["units"].add(unit)
            entry["ranges"].add((ref_min, ref_max))

            # Guardamos unos pocos ejemplos de líneas para contexto
            if len(entry["examples"]) < 5:
                entry["examples"].append({
                    "line": raw_line,
                    "value": value,
                    "ref_min": ref_min,
                    "ref_max": ref_max,
                    "unit": unit,
                })

    # Convertir sets a listas ordenadas para serializar a JSON
    serializable: Dict[str, Any] = {}
    for key, entry in params.items():
        serializable[key] = {
            "normalized_key": entry["normalized_key"],
            "original_names": sorted(entry["original_names"]),
            "units": sorted(entry["units"]),
            "ranges": sorted(
                [{"min": r[0], "max": r[1]} for r in entry["ranges"]],
                key=lambda d: (d["min"], d["max"])
            ),
            "examples": entry["examples"],
        }

    return serializable


def main():
    if len(sys.argv) < 3:
        print("Uso: python3.14 scan_lab_params.py <directorio_pdfs> <salida.json>")
        sys.exit(1)

    dir_path = sys.argv[1]
    out_path = sys.argv[2]

    if not os.path.isdir(dir_path):
        print(f"[ERROR] '{dir_path}' no es un directorio válido.")
        sys.exit(1)

    params = scan_directory(dir_path)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(params, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] Parámetros encontrados: {len(params)}")
    print(f"[OK] Fichero JSON generado: {out_path}")


if __name__ == "__main__":
    main()