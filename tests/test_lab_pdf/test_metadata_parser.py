from lab_pdf.metadata_parser import parse_metadata


def test_parse_metadata_from_sample_pdf(hemato_text: str):
    meta = parse_metadata(hemato_text)

    assert meta is not None
    # Ajusta la fecha si tu PDF de ejemplo tiene otra
    assert meta["fecha_analisis"] == "2025-11-13"
    assert meta["numero_peticion"] is not None
    assert isinstance(meta["numero_peticion"], str)
    assert meta["origen"] is not None
    assert isinstance(meta["origen"], str)
