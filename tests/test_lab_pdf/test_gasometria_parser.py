from lab_pdf.section_splitter import split_lab_sections
from lab_pdf.gasometria_parser import parse_gasometria_section


def test_gasometria_parser_extracts_basic_values(hemato_text: str):
    sections = split_lab_sections(hemato_text)

    # Algunos informes pueden no tener gasometría; si quisieras tolerarlo,
    # podrías hacer un `if "gasometria" not in sections: pytest.skip(...)`.
    gaso_text = sections["gasometria"]

    gaso = parse_gasometria_section(gaso_text)

    assert gaso["gaso_ph"] is not None
    # No forzamos un valor exacto por ahora, solo que exista
    assert 6.8 < gaso["gaso_ph"] < 7.8

    # Otros parámetros básicos que suelen estar
    assert gaso["gaso_pco2"] is not None
    assert gaso["gaso_po2"] is not None
