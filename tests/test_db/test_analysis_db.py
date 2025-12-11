# tests/test_db/test_analysis_db.py
# -*- coding: utf-8 -*-

import pytest


def test_create_and_list_analisis(analysis_db):
    a1_id = analysis_db.create_analisis(
        {
            "fecha_analisis": "2025-11-24",
            "numero_peticion": "PET-001",
            "origen": "HEMATOLOGIA",
        }
    )
    a2_id = analysis_db.create_analisis(
        {
            "fecha_analisis": "2025-11-25",
            "numero_peticion": "PET-002",
            "origen": "BIOQUIMICA",
        }
    )

    analisis_list = analysis_db.list_analisis()
    assert len(analisis_list) == 2
    ids = {row["id"] for row in analisis_list}
    assert a1_id in ids
    assert a2_id in ids


def test_patient_and_hematologia_flow(analysis_db):
    analysis_db.save_patient(
        {
            "nombre": "Borja",
            "apellidos": "Alonso Tristán",
            "fecha_nacimiento": "1985-06-15",
            "sexo": "M",
            "numero_historia": "HIST-999",
        }
    )
    paciente = analysis_db.get_patient()
    assert paciente is not None
    assert paciente["numero_historia"] == "HIST-999"

    analysis_db.insert_hematologia(
        {
            "fecha_analisis": "2025-11-27",
            "numero_peticion": "HEM-999",
            "origen": "HOSPITAL",
            "leucocitos": 4.8,
            "hemoglobina": 14.0,
            "plaquetas": 230,
        }
    )

    rows = analysis_db.list_hematologia()
    assert len(rows) == 1
    row = rows[0]
    assert row["numero_peticion"] == "HEM-999"
    assert row["leucocitos"] == 4.8


def test_create_analisis_without_fecha_raises(analysis_db):
    with pytest.raises(ValueError):
        analysis_db.create_analisis(
            {
                # falta fecha_analisis
                "numero_peticion": "NO-FECHA",
                "origen": "TEST",
            }
        )
