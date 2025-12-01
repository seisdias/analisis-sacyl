# -*- coding: utf-8 -*-
"""
Conversor de informes PDF de laboratorio a JSON de análisis de hematología,
bioquímica, gasometría y orina.

Autor: Borja Alonso Tristán
Año: 2025
"""

from __future__ import annotations

import re
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from PyPDF2 import PdfReader


# ============================================================
#   UTILIDADES GENERALES
# ============================================================

def _extract_text_from_pdf(pdf_path: str) -> str:
    """Extrae todo el texto de un PDF en una sola cadena."""
    reader = PdfReader(pdf_path)
    chunks = []
    for page in reader.pages:
        txt = page.extract_text() or ""
        chunks.append(txt)
    return "\n".join(chunks)


def _extract_float(pattern: str, texto: str) -> Optional[float]:
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


def _extract_named_value(label: str, texto: str) -> Optional[float]:
    """
    Extrae el primer valor numérico de una línea que empieza por 'label'.
    Ejemplo de línea:
        Sodio 138 mmol/L 136 - 146
    Buscamos el número inmediatamente después del nombre de la prueba.
    """
    pattern = rf"^{re.escape(label)}\s+([0-9]+(?:[.,][0-9]+)?)\s+"
    m = re.search(pattern, texto, flags=re.MULTILINE)
    if not m:
        return None
    valor_str = m.group(1).replace(",", ".")
    try:
        return float(valor_str)
    except ValueError:
        return None


def _extract_token(pattern: str, texto: str) -> Optional[str]:
    """
    Devuelve el primer grupo capturado como texto (limpio) o None si no hay match.
    Útil para campos cualitativos (NEGATIVO, TRAZAS, etc.)
    """
    m = re.search(pattern, texto, flags=re.IGNORECASE)
    if not m:
        return None
    return m.group(1).strip()


# ============================================================
#   METADATOS DE ANÁLISIS (FECHA, PETICIÓN, ORIGEN)
# ============================================================

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


def _parse_numero_peticion(texto: str) -> Optional[str]:
    """
    Extrae el 'Nº petición: XXXXX'. Devuelve None si no lo encuentra.
    """
    m = re.search(r"Nº petición:\s*([0-9A-Za-z]+)", texto)
    return m.group(1) if m else None


def _parse_origen(texto: str) -> Optional[str]:
    """
    Extrae el campo 'Origen: ...' en la parte del informe.
    """
    m = re.search(r"Origen:\s*(.+)", texto)
    if not m:
        return None
    linea = m.group(1)
    return linea.strip()


# ============================================================
#   DATOS DE PACIENTE
# ============================================================

PAT_NOMBRE = re.compile(r"Nombre:\s*(.*?)\s+Nº petición:", re.S)
PAT_APELLIDOS = re.compile(r"Apellidos:\s*(.*?)\s+Doctor:", re.S)
PAT_FECHA_SEXO = re.compile(r"Fecha nacimiento:\s*([\d/]+)\s+Sexo:\s*([MF])")
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


def _parse_patient(text: str) -> Dict[str, Any]:
    """
    Extrae los datos básicos del paciente a partir del texto completo del PDF.

    Devuelve un dict con:
      - nombre
      - apellidos
      - fecha_nacimiento (ISO YYYY-MM-DD si se puede)
      - sexo
      - numero_historia (solo si cumple patrón HURH...)
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
        raw_hist = m.group(1).strip()
        numero_historia = _clean_historia(raw_hist)

    return {
        "nombre": nombre,
        "apellidos": apellidos,
        "fecha_nacimiento": fecha_nacimiento,
        "sexo": sexo,
        "numero_historia": numero_historia,
    }


# ============================================================
#   HEMATOLOGÍA (HEMOGRAMA)
# ============================================================

def _parse_hematologia(texto: str, fecha_analisis: str,
                       numero_peticion: Optional[str],
                       origen: Optional[str]) -> Dict[str, Any]:
    """
    Extrae los datos de hemograma / hematología básica.
    Devuelve un dict (puede tener muchos campos a None si no aparecen).
    """

    # --- Serie blanca ---
    leucocitos = _extract_float(
        r"Leucocitos\s+\**([0-9]+(?:[.,][0-9]+)?)\s+x10\^3/µL", texto
    )

    neutrofilos_pct = _extract_float(
        r"Neutrófilos %\s+\**([0-9]+(?:[.,][0-9]+)?)\s+%", texto
    )
    linfocitos_pct = _extract_float(
        r"Linfocitos %\s+\**([0-9]+(?:[.,][0-9]+)?)\s+%", texto
    )
    monocitos_pct = _extract_float(
        r"Monocitos %\s+\**([0-9]+(?:[.,][0-9]+)?)\s+%", texto
    )
    eosinofilos_pct = _extract_float(
        r"Eosinófilos %\s+\**([0-9]+(?:[.,][0-9]+)?)\s+%", texto
    )
    basofilos_pct = _extract_float(
        r"Basófilos %\s+\**([0-9]+(?:[.,][0-9]+)?)\s+%", texto
    )

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
    hematies = _extract_float(
        r"Hematíes\s+\**([0-9]+(?:[.,][0-9]+)?)\s+x10\^6/µL", texto
    )
    hemoglobina = _extract_float(
        r"Hemoglobina\s+\**([0-9]+(?:[.,][0-9]+)?)\s+g/dL", texto
    )
    hematocrito = _extract_float(
        r"Hematocrito\s+\**([0-9]+(?:[.,][0-9]+)?)\s+%", texto
    )
    vcm = _extract_float(
        r"V\.C\.M\s+\**([0-9]+(?:[.,][0-9]+)?)\s+fL", texto
    )
    hcm = _extract_float(
        r"H\.C\.M\.\s+\**([0-9]+(?:[.,][0-9]+)?)\s+pg", texto
    )
    chcm = _extract_float(
        r"C\.H\.C\.M\.\s+\**([0-9]+(?:[.,][0-9]+)?)\s+g/dL", texto
    )
    rdw = _extract_float(
        r"R\.D\.W\s+\**([0-9]+(?:[.,][0-9]+)?)\s+%", texto
    )

    # --- Serie plaquetar ---
    plaquetas = _extract_float(
        r"Plaquetas\s+\**([0-9]+(?:[.,][0-9]+)?)\s+x10\^3/µL", texto
    )
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

    return analisis


# ============================================================
#   BIOQUÍMICA + VITAMINAS
# ============================================================

def _parse_bioquimica(texto: str, fecha_analisis: str,
                      numero_peticion: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    Extrae parámetros de bioquímica y vitaminas.
    Devuelve dict o None si no encuentra nada relevante.
    """
    data: Dict[str, Any] = {
        "fecha_analisis": fecha_analisis,
        "numero_peticion": numero_peticion,
    }

    # Valores básicos
    data["glucosa"] = _extract_float(r"Glucosa\s+\**([0-9]+(?:[.,][0-9]+)?)\s+", texto)
    data["urea"] = _extract_float(r"Urea\s+\**([0-9]+(?:[.,][0-9]+)?)\s+", texto)
    data["creatinina"] = _extract_float(r"Creatinina\s+\**([0-9]+(?:[.,][0-9]+)?)\s+", texto)

    data["sodio"] = _extract_float(r"Sodio\s+\**([0-9]+(?:[.,][0-9]+)?)\s+", texto)
    data["potasio"] = _extract_float(r"Potasio\s+\**([0-9]+(?:[.,][0-9]+)?)\s+", texto)
    data["cloro"] = _extract_float(r"Cloro\s+\**([0-9]+(?:[.,][0-9]+)?)\s+", texto)
    data["calcio"] = _extract_float(r"Calcio\s+\**([0-9]+(?:[.,][0-9]+)?)\s+", texto)
    data["fosforo"] = _extract_float(r"Fósforo\s+\**([0-9]+(?:[.,][0-9]+)?)\s+", texto)

    data["colesterol_total"] = _extract_float(
        r"Colesterol total\s+\**([0-9]+(?:[.,][0-9]+)?)\s+", texto
    )
    data["colesterol_hdl"] = _extract_float(
        r"Colesterol HDL\s+\**([0-9]+(?:[.,][0-9]+)?)\s+", texto
    )
    data["colesterol_ldl"] = _extract_float(
        r"Colesterol LDL\s+\**([0-9]+(?:[.,][0-9]+)?)\s+", texto
    )
    data["colesterol_no_hdl"] = _extract_float(
        r"Colesterol no HDL\s+\**([0-9]+(?:[.,][0-9]+)?)\s+", texto
    )
    data["trigliceridos"] = _extract_float(
        r"Triglicéridos\s+\**([0-9]+(?:[.,][0-9]+)?)\s+", texto
    )
    data["indice_riesgo"] = _extract_float(
        r"Índice riesgo\s+\**([0-9]+(?:[.,][0-9]+)?)\s+", texto
    )

    data["hierro"] = _extract_float(r"Hierro\s+\**([0-9]+(?:[.,][0-9]+)?)\s+", texto)
    data["ferritina"] = _extract_float(r"Ferritina\s+\**([0-9]+(?:[.,][0-9]+)?)\s+", texto)
    data["vitamina_b12"] = _extract_float(r"Vitamina\s+B12\s+\**([0-9]+(?:[.,][0-9]+)?)\s+", texto)

    # ¿Hay al menos un valor numérico?
    has_value = any(
        v is not None for k, v in data.items()
        if k not in ("fecha_analisis", "numero_peticion")
    )
    return data if has_value else None


# ============================================================
#   GASOMETRÍA
# ============================================================

def _parse_gasometria(texto: str, fecha_analisis: str,
                      numero_peticion: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    Parsea la sección de GASOMETRÍA (venosa/arterial) y devuelve un dict
    plano con los valores numéricos o None si no hay nada.
    """
    data: Dict[str, Any] = {
        "fecha_analisis": fecha_analisis,
        "numero_peticion": numero_peticion,
    }

    data["gaso_ph"] = _extract_named_value("pH", texto)
    data["gaso_pco2"] = _extract_named_value("pCO2", texto)
    data["gaso_po2"] = _extract_named_value("pO2", texto)
    data["gaso_tco2"] = _extract_named_value("CO2 Total (TCO2)", texto)

    data["gaso_so2_calc"] = _extract_named_value(
        "Saturación de Oxígeno (sO2) calculada", texto
    )
    data["gaso_so2"] = _extract_named_value(
        "Saturación de Oxígeno (sO2)", texto
    )

    data["gaso_p50"] = _extract_named_value("p50", texto)
    data["gaso_bicarbonato"] = _extract_named_value("Bicarbonato (CO3H-)", texto)
    data["gaso_sbc"] = _extract_named_value("Bicarbonato Estandar (SBC)", texto)
    data["gaso_eb"] = _extract_named_value("Exceso de Bases (EB)", texto)
    data["gaso_beecf"] = _extract_named_value(
        "E. de bases en fluido extracelular (BEecf)", texto
    )
    data["gaso_lactato"] = _extract_named_value("Lactato", texto)

    has_value = any(
        v is not None for k, v in data.items()
        if k not in ("fecha_analisis", "numero_peticion")
    )
    return data if has_value else None


# ============================================================
#   ORINA / URINOANÁLISIS
# ============================================================

def _parse_orina(texto: str, fecha_analisis: str,
                 numero_peticion: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    Extrae parámetros de orina / urinoanálisis.
    Devuelve dict o None si no encuentra nada relevante.
    """
    data: Dict[str, Any] = {
        "fecha_analisis": fecha_analisis,
        "numero_peticion": numero_peticion,
    }

    # Físico-químico
    data["ph"] = _extract_float(r"\bpH\s+\**([0-9]+(?:[.,][0-9]+)?)\s*", texto)
    data["densidad"] = _extract_float(r"Densidad\s+\**([0-9]+(?:[.,][0-9]+)?)\s*", texto)

    # Tiras / cualitativos (NEGATIVO, TRAZAS, +, etc.)
    data["glucosa"] = _extract_token(r"Glucosa\s+\**([A-Za-z+]+)", texto)
    data["proteinas"] = _extract_token(r"Proteínas\s+\**([A-Za-z+]+)", texto)
    data["cuerpos_cetonicos"] = _extract_token(r"Cuerpos cetónicos\s+\**([A-Za-z+]+)", texto)
    data["sangre"] = _extract_token(r"Sangre\s+\**([A-Za-z+]+)", texto)
    data["nitritos"] = _extract_token(r"Nitritos\s+\**([A-Za-z+]+)", texto)
    data["leucocitos_ests"] = _extract_token(r"Leucocitos esterasas?\s+\**([A-Za-z+]+)", texto)
    data["bilirrubina"] = _extract_token(r"Bilirrubina\s+\**([A-Za-z+]+)", texto)
    data["urobilinogeno"] = _extract_token(r"Urobilinógeno\s+\**([A-Za-z+]+)", texto)

    # Cuantitativos de orina (si los hubiera)
    data["sodio_ur"] = _extract_float(r"Sodio\s+orina\s+\**([0-9]+(?:[.,][0-9]+)?)\s+", texto)
    data["creatinina_ur"] = _extract_float(r"Creatinina\s+orina\s+\**([0-9]+(?:[.,][0-9]+)?)\s+", texto)
    data["indice_albumina_creatinina"] = _extract_float(
        r"Índice\s+Alb/Cre\s+\**([0-9]+(?:[.,][0-9]+)?)\s+", texto
    )
    data["albumina_ur"] = _extract_float(
        r"Albúmina\s+orina\s+\**([0-9]+(?:[.,][0-9]+)?)\s+", texto
    )
    data["categoria_albuminuria"] = _extract_token(
        r"Categoría\s+albuminuria\s+\**([A-Za-z0-9 ]+)", texto
    )

    # ¿Hay al menos algo informado?
    has_value = any(
        v is not None for k, v in data.items()
        if k not in ("fecha_analisis", "numero_peticion")
    )
    return data if has_value else None


# ============================================================
#   FUNCIÓN PRINCIPAL
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
    texto = _extract_text_from_pdf(pdf_path)

    # --- Datos de paciente ---
    paciente_data = _parse_patient(texto)

    # --- Metadatos comunes ---
    fecha_analisis = _parse_fecha_finalizacion(texto)
    numero_peticion = _parse_numero_peticion(texto)
    origen = _parse_origen(texto)  # de momento solo para hematología

    # --- Hematología ---
    hemat = _parse_hematologia(texto, fecha_analisis, numero_peticion, origen)

    # --- Bioquímica ---
    bio = _parse_bioquimica(texto, fecha_analisis, numero_peticion)

    # --- Gasometría ---
    gaso = _parse_gasometria(texto, fecha_analisis, numero_peticion)

    # --- Orina ---
    orina = _parse_orina(texto, fecha_analisis, numero_peticion)

    # Helper: ¿hay algún valor real en un dict?
    def _has_any_value(d: Dict[str, Any], ignore_keys=None) -> bool:
        if ignore_keys is None:
            ignore_keys = ()
        return any(
            v is not None
            for k, v in d.items()
            if k not in ignore_keys
        )

    has_hema = _has_any_value(hemat, ignore_keys=("fecha_analisis", "numero_peticion", "origen"))
    has_bio = bio is not None and _has_any_value(bio, ignore_keys=("fecha_analisis", "numero_peticion"))
    has_gaso = gaso is not None and _has_any_value(gaso, ignore_keys=("fecha_analisis", "numero_peticion"))
    has_orina = orina is not None and _has_any_value(orina, ignore_keys=("fecha_analisis", "numero_peticion"))

    if not (has_hema or has_bio or has_gaso or has_orina):
        # Hemocultivos u otros informes que no encajan
        raise ValueError(
            "El PDF no parece ser un informe de laboratorio (hemograma/bioquímica/"
            "gasometría/orina) reconocible y no se importará."
        )

    result: Dict[str, Any] = {
        "paciente": paciente_data or {},
    }

    if has_hema:
        result["hematologia"] = [hemat]
        # Compatibilidad con código antiguo (usa 'analisis')
        result["analisis"] = [hemat]

    if has_bio:
        result["bioquimica"] = [bio]

    if has_gaso:
        result["gasometria"] = [gaso]

    if has_orina:
        result["orina"] = [orina]

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