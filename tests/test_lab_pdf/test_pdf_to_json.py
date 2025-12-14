from pathlib import Path

import pytest

from lab_pdf.pdf_to_json import parse_hematology_pdf
from lab_pdf import pdf_to_json



def test_parse_hematology_pdf_complete_report(hemato_pdf_path: Path):
    data = parse_hematology_pdf(str(hemato_pdf_path))

    assert "paciente" in data
    assert isinstance(data["paciente"], dict)

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

from pathlib import Path

from lab_pdf.pdf_to_json import parse_hematology_pdf


def test_parse_hematology_pdf_anonymized_report_hema_and_bio_values():
    """
    Verifica que el parser extrae correctamente hematología y bioquímica
    desde un PDF anonimizado (sin datos personales reales).
    """
    from pathlib import Path
    import pytest

    # Import local (tal y como ya lo haces en este fichero)
    # Ajusta si tu import real es distinto:
    from lab_pdf.pdf_to_json import parse_hematology_pdf

    pdf_path = Path(__file__).resolve().parents[1] / "data" / "sample_lab_report_2025_06_24.pdf"
    assert pdf_path.exists(), f"No existe el PDF de test: {pdf_path}"

    data = parse_hematology_pdf(str(pdf_path))

    # Paciente: comprobamos que es ANONIMIZADO (no valores reales)
    assert "paciente" in data
    assert data["paciente"].get("nombre") in ("PACIENTE PRUEBA", "PACIENTE")  # depende de tu parse_patient
    assert data["paciente"].get("apellidos") in (None, "APELLIDO FICTICIO")

    # Debe haber hematología y bioquímica
    assert "hematologia" in data and len(data["hematologia"]) == 1
    assert "bioquimica" in data and len(data["bioquimica"]) == 1

    hema = data["hematologia"][0]
    bio = data["bioquimica"][0]

    # --- Hematología esperada ---
    assert hema["fecha_analisis"] == "2025-06-24"
    assert hema["numero_peticion"] == "65122928"
    assert hema["origen"] == "A. Primaria"

    assert hema["leucocitos"] == pytest.approx(2.4)
    assert hema["neutrofilos_pct"] == pytest.approx(20.2)
    assert hema["linfocitos_pct"] == pytest.approx(76.2)
    assert hema["monocitos_pct"] == pytest.approx(2.1)
    assert hema["eosinofilos_pct"] == pytest.approx(1.2)
    assert hema["basofilos_pct"] == pytest.approx(0.3)

    assert hema["neutrofilos_abs"] == pytest.approx(0.5)
    assert hema["linfocitos_abs"] == pytest.approx(1.8)
    assert hema["monocitos_abs"] == pytest.approx(0.0)
    assert hema["eosinofilos_abs"] == pytest.approx(0.0)
    assert hema["basofilos_abs"] == pytest.approx(0.0)

    assert hema["hematies"] == pytest.approx(3.56)
    assert hema["hemoglobina"] == pytest.approx(13.0)
    assert hema["hematocrito"] == pytest.approx(37.3)
    assert hema["vcm"] == pytest.approx(104.8)
    assert hema["hcm"] == pytest.approx(36.6)
    assert hema["chcm"] == pytest.approx(34.9)
    assert hema["rdw"] == pytest.approx(13.0)
    assert hema["plaquetas"] == pytest.approx(183.0)
    assert hema["vpm"] == pytest.approx(9.1)

    # --- Bioquímica esperada ---
    assert bio["fecha_analisis"] == "2025-06-24"
    assert bio["numero_peticion"] == "65122928"

    assert bio["glucosa"] == pytest.approx(84.0)
    assert bio["urea"] == pytest.approx(58.1)
    assert bio["creatinina"] == pytest.approx(0.82)
    assert bio["sodio"] == pytest.approx(139.0)
    assert bio["potasio"] == pytest.approx(4.1)
    assert bio["cloro"] == pytest.approx(105.0)
    assert bio["calcio"] == pytest.approx(9.4)
    assert bio["fosforo"] == pytest.approx(3.31)
    assert bio["acido_urico"] == pytest.approx(4.28)

    # Estos dos en tu JSON eran null (y en el PDF anonimizado NO los escribimos), así que deben ser None
    assert bio["ggt"] is None
    assert bio["ast_got"] is None

    assert bio["alt_gpt"] == pytest.approx(15.0)
    assert bio["fosfatasa_alcalina"] == pytest.approx(44.0)
    assert bio["bilirrubina_total"] == pytest.approx(1.16)

    assert bio["colesterol_total"] == pytest.approx(131.0)
    assert bio["colesterol_hdl"] == pytest.approx(58.0)
    assert bio["colesterol_ldl"] == pytest.approx(61.0)
    assert bio["colesterol_no_hdl"] == pytest.approx(73.0)
    assert bio["trigliceridos"] == pytest.approx(61.0)
    assert bio["indice_riesgo"] == pytest.approx(2.3)

    assert bio["hierro"] == pytest.approx(131.0)
    assert bio["ferritina"] == pytest.approx(552.2)
    assert bio["vitamina_b12"] == pytest.approx(196.6)
    assert bio["folico"] == pytest.approx(10.0)

