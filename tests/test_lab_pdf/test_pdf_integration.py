# tests/test_lab_pdf/test_pdf_integration.py

from pathlib import Path

import pytest

from lab_pdf import parse_hematology_pdf


def _hemato_pdf_path() -> Path:
    return Path(__file__).parents[1] / "data" / "12383248W_20251111.pdf"


def _hemocultivos_pdf_path() -> Path:
    return Path(__file__).parents[1] / "data" / "12383248W_20251108_hemocultivos.pdf"


def test_parse_hematology_pdf_complete_report():
    pdf_path = _hemato_pdf_path()
    data = parse_hematology_pdf(str(pdf_path))

    assert "paciente" in data
    assert "hematologia" in data
    assert "bioquimica" in data
    assert "gasometria" in data

    paciente = data["paciente"]
    assert paciente["nombre"] == "PACIENTE PRUEBA"
    assert paciente["apellidos"] == "APELLIDO FICTICIO"

    hema = data["hematologia"][0]
    assert hema["fecha_analisis"] == "2025-11-13"
    assert hema["numero_peticion"] == "00000001"
    assert hema["origen"] == "Hospital de Pruebas"
    assert hema["leucocitos"] == 0.4

    bio = data["bioquimica"][0]
    assert bio["sodio"] == 141.0
    assert bio["glucosa"] == 106.0

    gaso = data["gasometria"][0]
    assert float(gaso["gaso_ph"]) == 7.41


def test_parse_hematology_pdf_hemocultivos_raises():
    pdf_path = _hemocultivos_pdf_path()
    with pytest.raises(ValueError):
        parse_hematology_pdf(str(pdf_path))
