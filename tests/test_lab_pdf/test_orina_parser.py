import pytest

from lab_pdf.section_splitter import split_lab_sections
from lab_pdf.orina_parser import parse_orina_section


@pytest.mark.skip("Activar cuando tengamos un PDF de ejemplo con orina")
def test_orina_parser_extracts_basic_values(hemato_text: str):
    sections = split_lab_sections(hemato_text)

    assert "orina" in sections, "El PDF de ejemplo no contiene sección de orina"
    orina_text = sections["orina"]

    orina = parse_orina_section(orina_text)

    assert orina["ph"] is not None
    assert orina["densidad"] is not None

def test_orina_parser_extracts_quantitative_and_qualitative_values():
    # Texto sintético que simula la sección de orina de un informe
    texto = """
    pH 6.0
    Densidad 1020

    Glucosa NEGATIVO
    Proteínas +
    Cuerpos cetónicos TRAZAS
    Sangre ++
    Nitritos NEGATIVO
    Leucocitos esterasas +
    Bilirrubina NEGATIVO
    Urobilinógeno NORMAL

    Sodio orina 140 mmol/L 40 - 220
    Creatinina orina 110 mg/dL 20 - 300
    Índice Alb/Cre 30 mg/g 0 - 30
    Albúmina orina 25 mg/L 0 - 30
    Categoría albuminuria A1
    """

    data = parse_orina_section(texto)

    # Físico-químico
    assert data["ph"] == 6.0
    assert data["densidad"] == 1020

    # Cualitativos (tiras)
    assert data["glucosa"] == "NEGATIVO"
    assert data["proteinas"] == "+"
    assert data["cuerpos_cetonicos"] == "TRAZAS"
    assert data["sangre"] == "++"
    assert data["nitritos"] == "NEGATIVO"
    assert data["leucocitos_ests"] == "+"
    assert data["bilirrubina"] == "NEGATIVO"
    assert data["urobilinogeno"] == "NORMAL"

    # Cuantitativos
    assert data["sodio_ur"] == 140.0
    assert data["creatinina_ur"] == 110.0
    assert data["indice_albumina_creatinina"] == 30.0
    assert data["albumina_ur"] == 25.0
    assert data["categoria_albuminuria"] == "A1"


def test_orina_parser_returns_none_when_no_values():
    texto = "Este texto no contiene parámetros de orina relevantes"
    data = parse_orina_section(texto)

    # Si tu parser devuelve None cuando no encuentra nada, dejamos esto así.
    # Si en vez de None devuelve un dict vacío, cambia la aserción.
    assert data is None or all(
        v is None for k, v in data.items() if k not in ("fecha_analisis", "numero_peticion")
    )

