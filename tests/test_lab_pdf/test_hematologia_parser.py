from lab_pdf.section_splitter import split_lab_sections
from lab_pdf.hematologia_parser import parse_hematologia_section


def test_hematologia_parser_extracts_basic_values(hemato_text: str):
    sections = split_lab_sections(hemato_text)
    hema_text = sections["hematologia"]

    hema = parse_hematologia_section(hema_text)

    assert hema["leucocitos"] is not None
    assert hema["hemoglobina"] is not None
    assert hema["hematocrito"] is not None
    assert hema["plaquetas"] is not None

    # Valores numéricos coherentes
    assert hema["leucocitos"] > 0
    assert hema["hemoglobina"] > 0
    assert hema["plaquetas"] > 0
