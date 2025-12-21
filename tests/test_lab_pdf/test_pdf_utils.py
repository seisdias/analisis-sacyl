from lab_pdf.pdf_utils import extract_text_from_pdf, has_any_value


def test_extract_text_from_pdf_returns_non_empty_string(hemato_pdf_path):
    texto = extract_text_from_pdf(str(hemato_pdf_path))
    assert isinstance(texto, str)
    assert len(texto) > 0
    # Alguna marca típica del informe
    assert "Recepción:" in texto

def test_has_any_value_ignores_metadata_keys():
    data = {
        "fecha_analisis": "2025-11-13",
        "numero_peticion": "00000002",
        "origen": "HEMATOLOGIA",
        "glucosa": None,
        "sodio": 141.0,
    }

    assert has_any_value(data, ignore_keys=("fecha_analisis", "numero_peticion", "origen")) is True

    data2 = {
        "fecha_analisis": "2025-11-13",
        "numero_peticion": "00000002",
        "origen": "HEMATOLOGIA",
        "glucosa": None,
        "sodio": None,
    }

    assert has_any_value(data2, ignore_keys=("fecha_analisis", "numero_peticion", "origen")) is False


