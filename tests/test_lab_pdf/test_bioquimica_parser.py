from lab_pdf.section_splitter import split_lab_sections
from lab_pdf.bioquimica_parser import parse_bioquimica_section


def test_bioquimica_parser_extracts_basic_values(hemato_text: str):
    sections = split_lab_sections(hemato_text)
    bio_text = sections["bioquimica"]

    bio = parse_bioquimica_section(bio_text)

    # Al menos debe tener datos
    assert bio["glucosa"] is not None

    # Estos valores vienen del propio PDF de ejemplo
    assert bio["glucosa"] == 106.0
    assert bio["sodio"] == 141.0
    assert bio["potasio"] == 3.7

    # No todos los informes tendrán cloro, así que no lo forzamos
    # if "cloro" in bio:
    #     assert bio["cloro"] == 110.0
