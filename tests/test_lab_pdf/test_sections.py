# tests/test_lab_pdf/test_sections.py

from pathlib import Path

from lab_pdf.section_splitter import split_lab_sections
from lab_pdf.hematologia_parser import parse_hematologia_section
from lab_pdf.bioquimica_parser import parse_bioquimica_section
from lab_pdf.gasometria_parser import parse_gasometria_section
from lab_pdf.orina_parser import parse_orina_section
from lab_pdf.pdf_utils import extract_text_from_pdf, has_any_value


def _hemato_text() -> str:
    path = Path(__file__).parents[1] / "data" / "12383248W_20251111.pdf"
    return extract_text_from_pdf(str(path))


def test_split_lab_sections_detects_main_sections():
    texto = _hemato_text()
    sections = split_lab_sections(texto)

    assert "hematologia" in sections
    assert "bioquimica" in sections
    assert "gasometria" in sections
    # No hemos puesto sección de orina en el PDF ficticio
    assert "orina" not in sections


def test_hematologia_parser_extracts_basic_values():
    texto = _hemato_text()
    sections = split_lab_sections(texto)
    hemat_text = sections["hematologia"]

    hema = parse_hematologia_section(hemat_text)
    assert has_any_value(hema)

    assert hema["leucocitos"] == 0.4
    assert hema["linfocitos_pct"] == 98.7
    assert hema["plaquetas"] == 150.0


def test_bioquimica_parser_extracts_basic_values():
    texto = _hemato_text()
    sections = split_lab_sections(texto)
    bio_text = sections["bioquimica"]

    bio = parse_bioquimica_section(bio_text)
    assert has_any_value(bio)

    assert bio["glucosa"] == 106.0
    assert bio["sodio"] == 141.0
    assert bio["potasio"] == 3.7
    assert bio["cloro"] == 110.0
    assert bio["creatinina"] == 0.68


def test_gasometria_parser_extracts_basic_values():
    texto = _hemato_text()
    sections = split_lab_sections(texto)
    gaso_text = sections["gasometria"]

    gaso = parse_gasometria_section(gaso_text)
    assert has_any_value(gaso)

    assert float(gaso["gaso_ph"]) == 7.41
