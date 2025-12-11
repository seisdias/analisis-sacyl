from lab_pdf.patient_parser import parse_patient


def test_parse_patient_from_sample_pdf(hemato_text: str):
    paciente = parse_patient(hemato_text)

    assert paciente is not None
    assert paciente["nombre"] is not None
    assert isinstance(paciente["nombre"], str)
    assert paciente["apellidos"] is not None

    # Fecha de nacimiento parseada a ISO o, como mínimo, presente
    assert paciente["fecha_nacimiento"] is not None

    # Sexo M/F
    assert paciente["sexo"] in ("M", "F")

    # Nº de historia: puede ser None si no cumple el patrón, o HURHxxxx...
    nh = paciente["numero_historia"]
    if nh is not None:
        assert nh.startswith("HURH")
