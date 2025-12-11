# tests/test_db/test_hematologia.py
# -*- coding: utf-8 -*-


def test_insert_and_list(components):
    hematologia = components["hematologia"]

    data = {
        "fecha_analisis": "2025-11-24",
        "numero_peticion": "PET-100",
        "origen": "HEM",
        "leucocitos": 5.2,
        "hemoglobina": 13.5,
        "plaquetas": 250,
    }
    hematologia.insert(data)

    rows = hematologia.list()
    assert len(rows) == 1
    row = rows[0]

    assert row["fecha_analisis"] == "2025-11-24"
    assert row["numero_peticion"] == "PET-100"
    assert row["origen"] == "HEM"
    assert row["leucocitos"] == 5.2
    assert row["hemoglobina"] == 13.5
    assert row["plaquetas"] == 250


def test_limit_in_list(components):
    hematologia = components["hematologia"]

    for i in range(3):
        hematologia.insert(
            {
                "fecha_analisis": f"2025-11-2{i}",
                "numero_peticion": f"PET-{i}",
                "origen": "HEM",
                "leucocitos": 4.0 + i,
            }
        )

    rows_all = hematologia.list()
    rows_lim = hematologia.list(limit=2)

    assert len(rows_all) == 3
    assert len(rows_lim) == 2
