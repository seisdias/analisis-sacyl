from pathlib import Path

import pytest

from lab_pdf.pdf_to_json import parse_hematology_pdf
from lab_pdf import pdf_to_json



def test_parse_hematology_pdf_complete_report(hemato_pdf_path: Path):
    data = parse_hematology_pdf(str(hemato_pdf_path))

    assert "paciente" in data
    assert isinstance(data["paciente"], dict)

    # Compatibilidad antigua: 'analisis' y nueva clave 'hematologia'
    assert "analisis" in data
    assert isinstance(data["analisis"], list)
    assert len(data["analisis"]) >= 1

    assert "hematologia" in data
    assert isinstance(data["hematologia"], list)
    assert len(data["hematologia"]) >= 1


def test_parse_hematology_pdf_hemocultivos_raises(hemocultivos_pdf_path: Path):
    """
    El informe de hemocultivos NO debe ser tratado como hemograma/bioquímica/gasometría/orina,
    y parse_hematology_pdf debe lanzar ValueError.
    """
    with pytest.raises(ValueError):
        parse_hematology_pdf(str(hemocultivos_pdf_path))

def _fake_metadata_header() -> str:
    return (
        "Nombre: PACIENTE PRUEBA      Nº petición: 00000002\n"
        "Apellidos: APELLIDO FICTICIO      Doctor: DR PRUEBA\n"
        "Fecha nacimiento: 23/06/1980   Sexo: M\n"
        "Nº Historia: HURH123456\n"
        "Finalización: 13/11/25\n"
        "Origen: HEMATOLOGIA\n"
    )


def test_parse_hematology_pdf_only_bioquimica(monkeypatch, tmp_path):
    """
    Texto sintético con líneas de bioquímica, pero SIN encabezados reales de sección.
    Con las reglas actuales de split_lab_sections esto NO se reconoce como informe
    estándar de hemograma/bioquímica/gasometría/orina, por lo que debe lanzar ValueError.
    """

    fake_text = _fake_metadata_header() + """
    --- BIOQUIMICA ---
    Glucosa 90 mg/dL 70 - 110
    Sodio 140 mmol/L 136 - 146
    Potasio 4.0 mmol/L 3.5 - 5.1
    """

    def fake_extract(path: str) -> str:
        # Ignoramos el path, devolvemos siempre nuestro texto sintético
        return fake_text

    # Parcheamos la función de extracción de texto
    monkeypatch.setattr(pdf_to_json, "extract_text_from_pdf", fake_extract)

    fake_pdf = tmp_path / "dummy.pdf"
    fake_pdf.write_text("no importa", encoding="utf-8")

    # Con encabezados irreales, el parser considera que no hay bloques válidos
    with pytest.raises(ValueError):
        parse_hematology_pdf(str(fake_pdf))


def test_parse_hematology_pdf_only_orina(monkeypatch, tmp_path):
    """
    Simula un informe con solo orina para ejercitar el camino 'orina' sin
    hematología/bioquímica/gasometría, usando encabezado de sección reconocible.
    """

    fake_text = _fake_metadata_header() + """
    ORINA:
    pH 5.5
    Densidad 1030
    Glucosa NEGATIVO
    Proteínas NEGATIVO
    """

    def fake_extract(path: str) -> str:
        return fake_text

    monkeypatch.setattr(pdf_to_json, "extract_text_from_pdf", fake_extract)

    fake_pdf = tmp_path / "dummy_orina.pdf"
    fake_pdf.write_text("no importa", encoding="utf-8")

    data = parse_hematology_pdf(str(fake_pdf))

    assert "orina" in data
    assert len(data["orina"]) == 1

    orina = data["orina"][0]
    assert orina["ph"] == 5.5
    assert orina["densidad"] == 1030

    # No debería haberse creado 'analisis' ni 'hematologia'
    assert "hematologia" not in data
    assert "analisis" not in data
    assert "bioquimica" not in data
    assert "gasometria" not in data


def test_parse_hematology_pdf_no_recognized_sections_raises(monkeypatch, tmp_path):
    """
    Simula un informe sin secciones reconocibles (ni hemato, ni bioquímica, ni gaso, ni orina).
    Debe lanzar ValueError según la lógica actual.
    """

    fake_text = _fake_metadata_header() + """
    INFORME ESPECIAL DE MICROBIOLOGÍA
    Texto libre sin parámetros de laboratorio estándar.
    """

    def fake_extract(path: str) -> str:
        return fake_text

    monkeypatch.setattr(pdf_to_json, "extract_text_from_pdf", fake_extract)

    fake_pdf = tmp_path / "dummy_empty.pdf"
    fake_pdf.write_text("no importa", encoding="utf-8")

    with pytest.raises(ValueError):
        parse_hematology_pdf(str(fake_pdf))
