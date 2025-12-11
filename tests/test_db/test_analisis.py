# tests/test_db/test_analisis.py
# -*- coding: utf-8 -*-


def test_create_and_list_single(components):
    analisis = components["analisis"]

    data = {
        "fecha_analisis": "2025-11-24",
        "numero_peticion": "PET-001",
        "origen": "HEMATOLOGIA",
    }
    new_id = analisis.create(data)
    assert isinstance(new_id, int)

    rows = analisis.list()
    assert len(rows) == 1
    row = rows[0]
    assert row["id"] == new_id
    assert row["fecha_analisis"] == "2025-11-24"
    assert row["numero_peticion"] == "PET-001"
    assert row["origen"] == "HEMATOLOGIA"


def test_ensure_with_existing_id(components):
    analisis = components["analisis"]

    new_id = analisis.create(
        {
            "fecha_analisis": "2025-11-24",
            "numero_peticion": "PET-002",
            "origen": "GASOMETRIA",
        }
    )
    ensured_id = analisis.ensure({"analisis_id": new_id})
    assert ensured_id == new_id
