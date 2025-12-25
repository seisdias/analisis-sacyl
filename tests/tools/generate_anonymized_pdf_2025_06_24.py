# -*- coding: utf-8 -*-
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4


def write_lines(c, x, y, lines, leading=14):
    for line in lines:
        # Si la línea es un encabezado de sección, la ponemos en negrita (opcional)
        c.drawString(x, y, line)
        y -= leading
    return y


def main():
    # Directorio de salida según tu estructura de tests
    out_dir = Path("tests/data")
    out_dir.mkdir(parents=True, exist_ok=True)

    # Nombre del archivo que esperan tus tests
    out_pdf = out_dir / "hemocultivos_20251113.pdf"

    c = canvas.Canvas(str(out_pdf), pagesize=A4)
    width, height = A4

    y = height - 60
    c.setFont("Helvetica", 10)

    # --- CABECERA (Actualizada con Recepción) ---
    header = [
        "Nombre: PACIENTE PRUEBA      Nº petición: 00000001",
        "Apellidos: APELLIDO FICTICIO  Doctor: DR PRUEBA",
        "Fecha nacimiento: 01/01/1980  Sexo: M  Nº Historia: HURH000001",
        "Recepción: 13/11/25          Origen: Hospital de Pruebas",  # CAMBIO CLAVE AQUÍ
        "",
    ]
    y = write_lines(c, 50, y, header)

    # --- HEMATOLOGÍA ---
    hema = [
        "HEMATOLOGÍA",
        "Leucocitos 0.4 x10^3/µL 4.0 - 10.5",
        "Neutrófilos % 1.0 % 40.0 - 74.0",
        "Linfocitos % 98.7 % 20.0 - 51.0",
        "Monocitos % 0.3 % 2.0 - 12.0",
        "Eosinófilos % 0.0 % 0.0 - 7.0",
        "Basófilos % 0.0 % 0.0 - 2.0",
        "Neutrófilos 0.0 x10^3/µL 1.6 - 7.5",
        "Linfocitos 0.4 x10^3/µL 1.0 - 4.0",
        "Monocitos 0.0 x10^3/µL 0.2 - 0.8",
        "Eosinófilos 0.0 x10^3/µL 0.02 - 0.5",
        "Basófilos 0.0 x10^3/µL 0.0 - 0.2",
        "Hematíes 4.50 x10^6/µL 4.20 - 5.90",
        "Hemoglobina 13.5 g/dL 13.0 - 17.0",
        "Hematocrito 40.0 % 40.0 - 54.0",
        "V.C.M 90.0 fL 80.0 - 96.0",
        "H.C.M. 30.0 pg 27.0 - 33.0",
        "C.H.C.M. 33.0 g/dL 32.0 - 36.0",
        "R.D.W 12.0 % 11.5 - 14.5",
        "Plaquetas 150 x10^3/µL 150 - 450",
        "Volumen Plaquetar Medio 9.0 fL 7.0 - 11.0",
        "",
    ]
    y = write_lines(c, 50, y, hema)

    # --- BIOQUÍMICA ---
    bio = [
        "BIOQUÍMICA",
        "Glucosa 106 mg/dL",
        "Urea 30 mg/dL",
        "Creatinina 0.68 mg/dL",
        "Sodio 141 mmol/L",
        "Potasio 3.7 mmol/L",
        "Cloro 110 mmol/L",
        "Calcio 9.5 mg/dL",
        "Fósforo 3.5 mg/dL",
        "Colesterol total 180 mg/dL",
        "Colesterol HDL 50 mg/dL",
        "Colesterol LDL 110 mg/dL",
        "Colesterol no HDL 130 mg/dL",
        "Triglicéridos 120 mg/dL",
        "Índice riesgo 3.6",
        "Hierro 80 µg/dL",
        "Ferritina 150 ng/mL",
        "Vitamina B12 400 pg/mL",
        "",
    ]
    y = write_lines(c, 50, y, bio)

    # --- GASOMETRÍA ---
    gaso = [
        "GASOMETRÍA",
        "pH 7.41 7.32 - 7.42",
        "pCO2 39 mmHg 41 - 51",
        "pO2 80 mmHg 25 - 40",
        "CO2 Total (TCO2) 25.9 mmol/L 27 - 33",
        "Saturación de Oxígeno (sO2) 96 % 90 - 100",
        "Bicarbonato (CO3H-) 24.0 mmol/L 22 - 26",
        "Bicarbonato Estandar (SBC) 24.0 mmol/L 22 - 26",
        "Exceso de Bases (EB) 0.0 mmol/L -2 - +2",
        "E. de bases en fluido extracelular (BEecf) 0.0 mmol/L -2 - +2",
        "Lactato 1.0 mmol/L 0.5 - 2.2",
    ]
    write_lines(c, 50, y, gaso)

    c.save()
    print(f"✅ PDF regenerado con éxito en: {out_pdf}")


if __name__ == "__main__":
    main()