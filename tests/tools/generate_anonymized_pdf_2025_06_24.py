# -*- coding: utf-8 -*-
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

def write_lines(c, x, y, lines, leading=14):
    for line in lines:
        c.drawString(x, y, line)
        y -= leading
    return y

def main():
    out_dir = Path("tests/data")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_pdf = out_dir / "sample_lab_report_2025_06_24.pdf"

    c = canvas.Canvas(str(out_pdf), pagesize=A4)
    width, height = A4

    y = height - 60
    c.setFont("Helvetica", 11)

    # --- Cabecera ANONIMIZADA (pero con fecha/petición/origen para que el parser funcione) ---
    header = [
        "Nombre: PACIENTE PRUEBA      Nº petición: 65122928",
        "Apellidos: APELLIDO FICTICIO  Doctor: DOCTOR NO",
        "Fecha nacimiento: 01/01/1980  Sexo: M  Origen: A. Primaria",
        "Recepción: 24/06/25  Finalización: 24/06/25",
        "",
    ]
    y = write_lines(c, 50, y, header)

    # --- Hematología (valores del JSON que pegaste) ---
    hema = [
        "HEMATOLOGÍA",
        "SERIE BLANCA",
        "Leucocitos * 2.4 x10^3/µL 4 - 10.5",
        "Neutrófilos % * 20.2 % 41 - 72",
        "Linfocitos % ** 76.2 % 20 - 51",
        "Monocitos % 2.1 % 2 - 12",
        "Eosinófilos % 1.2 % 0 - 8",
        "Basófilos % 0.3 % 0 - 1.8",
        "Neutrófilos * 0.5 x10^3/µL 1.5 - 7.5",
        "Linfocitos 1.8 x10^3/µL 0.9 - 5.2",
        "Monocitos * 0.0 x10^3/µL 0.2 - 1.1",
        "Eosinófilos 0.0 x10^3/µL 0.1 - 0.65",
        "Basófilos 0.0 x10^3/µL 0 - 0.2",
        "",
        "SERIE ROJA",
        "Hematíes 3.56 x10^6/µL 4.2 - 5.8",
        "Hemoglobina 13.0 g/dL 13.5 - 17.5",
        "Hematocrito 37.3 % 40 - 52",
        "V.C.M 104.8 fL 80 - 96",
        "H.C.M. 36.6 pg 27 - 33",
        "C.H.C.M. 34.9 g/dL 32 - 36",
        "R.D.W 13.0 % 11.5 - 14.5",
        "",
        "SERIE PLAQUETAR",
        "Plaquetas 183 x10^3/µL 150 - 400",
        "Volumen Plaquetar Medio 9.1 fL 7.4 - 10.4",
        "",
    ]
    y = write_lines(c, 50, y, hema)

    # Salto de página para ayudar al splitter
    c.showPage()
    c.setFont("Helvetica", 11)
    y = height - 60

    # --- Bioquímica (valores del JSON que pegaste) ---
    bio = [
        "BIOQUÍMICA EN SANGRE",
        "Prueba Resultado Unidades Valores de referencia",
        "Glucosa 84 mg/dL 74 - 110",
        "Urea * 58.1 mg/dL 12.8 - 42.8",
        "Creatinina 0.82 mg/dL 0.7 - 1.3",
        "Sodio 139 mmol/L 136 - 146",
        "Potasio 4.1 mmol/L 3.5 - 5.1",
        "Cloruro 105 mmol/L 101 - 109",
        "Calcio 9.4 mg/dL 8.6 - 10.2",
        "Fosfato 3.31 mg/dL 2.4 - 4.4",
        "Ácido úrico 4.28 mg/dL 3.5 - 7.2",
        "Alanina aminotransferasa (ALT/GPT) 15 U/L 1 - 50",
        "Fosfatasa alcalina 44 U/L 40 - 129",
        "Bilirrubina total 1.16 mg/dL 0.3 - 1.2",
        "",
        "Colesterol total 131 mg/dL",
        "Colesterol HDL 58 mg/dL",
        "Colesterol LDL 61 mg/dL",
        "Colesterol no HDL 73 mg/dL",
        "Triglicéridos 61 mg/dL",
        "Indice de riesgo cardiovascular 2.3",
        "",
        "Hierro 131 µg/dL",
        "Ferritina 552.2 ng/mL",
        "Vitamina B12 196.6 pg/mL",
        "Ácido fólico 10.0 ng/mL",
        "",
    ]
    write_lines(c, 50, y, bio)

    c.save()
    print(f"OK -> {out_pdf}")

if __name__ == "__main__":
    main()
