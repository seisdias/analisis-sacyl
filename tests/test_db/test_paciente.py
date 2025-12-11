# tests/test_db/test_paciente.py
# -*- coding: utf-8 -*-


def test_save_and_get_patient(components):
    paciente = components["paciente"]

    info = {
        "nombre": "Borja",
        "apellidos": "Alonso Tristán",
        "fecha_nacimiento": "1985-06-15",
        "sexo": "M",
        "numero_historia": "HIST-123",
    }
    paciente.save(info)

    row = paciente.get()
    assert row is not None
    assert row["nombre"] == "Borja"
    assert row["apellidos"] == "Alonso Tristán"
    assert row["numero_historia"] == "HIST-123"


def test_save_overwrites_previous_patient(components):
    paciente = components["paciente"]

    paciente.save(
        {
            "nombre": "Paciente1",
            "apellidos": "Uno",
            "fecha_nacimiento": "1990-01-01",
            "sexo": "M",
            "numero_historia": "H1",
        }
    )
    paciente.save(
        {
            "nombre": "Paciente2",
            "apellidos": "Dos",
            "fecha_nacimiento": "1995-02-02",
            "sexo": "F",
            "numero_historia": "H2",
        }
    )

    row = paciente.get()
    assert row is not None
    assert row["nombre"] == "Paciente2"
    assert row["numero_historia"] == "H2"
