# tests/test_lab_pdf/test_metadata_patient.py

from lab_pdf.metadata_parser import parse_metadata
from lab_pdf.patient_parser import parse_patient
from lab_pdf.pdf_utils import extract_text_from_pdf


def _load_hemato_text() -> str:
    from pathlib import Path
    path = Path(__file__).parents[1] / "data" / "12383248W_20251111.pdf"
    return extract_text_from_pdf(str(path))


def test_parse_metadata_from_sample_pdf():
    texto = _load_hemato_text()
    meta = parse_metadata(texto)

    assert meta["fecha_analisis"] == "2025-11-13"   # Finalización: 13/11/25
    assert meta["numero_peticion"] == "00000001"
    assert meta["origen"] == "Hospital de Pruebas"


def test_parse_patient_from_sample_pdf():
    texto = _load_hemato_text()
    patient = parse_patient(texto)

    assert patient["nombre"] == "PACIENTE PRUEBA"
    assert patient["apellidos"] == "APELLIDO FICTICIO"
    assert patient["fecha_nacimiento"] == "1980-01-01"
    assert patient["sexo"] == "M"
    assert patient["numero_historia"] == "HURH000001"
