from lab_pdf.section_splitter import split_lab_sections


def test_split_lab_sections_detects_main_sections(hemato_text: str):
    sections = split_lab_sections(hemato_text)

    # Secciones principales que esperamos en este informe
    assert "hematologia" in sections
    assert "bioquimica" in sections
    assert "gasometria" in sections

    # La sección de orina puede o no estar presente según el informe;
    # si el PDF de ejemplo la tiene, podrías activar esta línea:
    # assert "orina" in sections
