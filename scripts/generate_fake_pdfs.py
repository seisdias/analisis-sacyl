# scripts/generate_fake_pdfs.py
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def write_pdf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(path), pagesize=A4)
    width, height = A4
    x_margin = 40
    y = height - 40

    for line in text.splitlines():
        c.drawString(x_margin, y, line)
        y -= 14
        if y < 40:
            c.showPage()
            y = height - 40
    c.save()


HEMATO_PDF_TEXT = """\
Nombre: PACIENTE PRUEBA      Nº petición: 00000001
Apellidos: APELLIDO FICTICIO      Doctor: DR PRUEBA
Fecha nacimiento: 01/01/1980   Sexo: M
Nº Historia: HURH000001

Finalización: 13/11/25
Origen: Hospital de Pruebas

HEMATOLOGÍA
Leucocitos 0.4 x10^3/µL     4.0 - 10.5
Neutrófilos % 1.0 %         40.0 - 74.0
Linfocitos % 98.7 %         20.0 - 51.0
Monocitos % 0.3 %           2.0 - 12.0
Eosinófilos % 0.0 %         0.0 - 7.0
Basófilos % 0.0 %           0.0 - 2.0

Neutrófilos 0.0 x10^3/µL    1.6 - 7.5
Linfocitos 0.4 x10^3/µL     1.0 - 4.0
Monocitos 0.0 x10^3/µL      0.2 - 0.8
Eosinófilos 0.0 x10^3/µL    0.02 - 0.5
Basófilos 0.0 x10^3/µL      0.0 - 0.2

Hematíes 4.50 x10^6/µL      4.20 - 5.90
Hemoglobina 13.5 g/dL       13.0 - 17.0
Hematocrito 40.0 %          40.0 - 54.0
V.C.M 90.0 fL               80.0 - 96.0
H.C.M. 30.0 pg              27.0 - 33.0
C.H.C.M. 33.0 g/dL          32.0 - 36.0
R.D.W 12.0 %                11.5 - 14.5

Plaquetas 150 x10^3/µL      150 - 450
Volumen Plaquetar Medio 9.0 fL   7.0 - 11.0

BIOQUÍMICA
Glucosa 106 mg/dL
Urea 30 mg/dL
Creatinina 0.68 mg/dL
Sodio 141 mmol/L
Potasio 3.7 mmol/L
Cloro 110 mmol/L
Calcio 9.5 mg/dL
Fósforo 3.5 mg/dL

Colesterol total 180 mg/dL
Colesterol HDL 50 mg/dL
Colesterol LDL 110 mg/dL
Colesterol no HDL 130 mg/dL
Triglicéridos 120 mg/dL
Índice riesgo 3.6

Hierro 80 µg/dL
Ferritina 150 ng/mL
Vitamina B12 400 pg/mL

GASOMETRÍA
pH 7.41             7.32 - 7.42
pCO2 39 mmHg        41 - 51
pO2 80 mmHg         25 - 40
CO2 Total (TCO2) 25.9 mmol/L 27 - 33
Saturación de Oxígeno (sO2) 96 % 90 - 100
Bicarbonato (CO3H-) 24.0 mmol/L 22 - 26
Bicarbonato Estandar (SBC) 24.0 mmol/L 22 - 26
Exceso de Bases (EB) 0.0 mmol/L -2 - +2
E. de bases en fluido extracelular (BEecf) 0.0 mmol/L -2 - +2
Lactato 1.0 mmol/L 0.5 - 2.2
"""


HEMOCULTIVOS_PDF_TEXT = """\
Nombre: PACIENTE PRUEBA      Nº petición: 00000002
Apellidos: APELLIDO FICTICIO      Doctor: DR PRUEBA
Fecha nacimiento: 01/01/1980   Sexo: M
Nº Historia: HURH000001

Finalización: 14/11/25
Origen: Hospital de Pruebas

HEMOCULTIVOS

Muestras: 2 frascos aerobios, 2 frascos anaerobios.
Resultado: NO desarrollo bacteriano significativo tras 5 días de incubación.
Interpretación: Hemocultivos NEGATIVOS.
"""

if __name__ == "__main__":
    base_dir = Path(__file__).parents[1] / "tests" / "data"

    hemato_pdf = base_dir / "12383248W_20251111.pdf"
    hemocultivos_pdf = base_dir / "12383248W_20251108_hemocultivos.pdf"

    write_pdf(hemato_pdf, HEMATO_PDF_TEXT)
    write_pdf(hemocultivos_pdf, HEMOCULTIVOS_PDF_TEXT)

    print("Generado:", hemato_pdf)
    print("Generado:", hemocultivos_pdf)
