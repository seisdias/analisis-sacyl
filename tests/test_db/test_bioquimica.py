# tests/test_db/test_bioquimica.py
# -*- coding: utf-8 -*-


def test_insert_and_list_bioquimica(components):
    bioquimica = components["bioquimica"]

    data = {
        "fecha_analisis": "2025-11-24",
        "numero_peticion": "BIO-001",
        "origen": "BIO",
        "glucosa": 90.0,
        "urea": 30.0,
        "creatinina": 0.9,
    }
    bioquimica.insert(data)

    rows = bioquimica.list()
    assert len(rows) == 1

    row = rows[0]
    assert row["fecha_analisis"] == "2025-11-24"
    assert row["numero_peticion"] == "BIO-001"
    assert row["origen"] == "BIO"
    assert row["glucosa"] == 90.0
    assert row["urea"] == 30.0
    assert row["creatinina"] == 0.9


def test_limit_in_list_bioquimica(components):
    bioquimica = components["bioquimica"]

    for i in range(3):
        bioquimica.insert(
            {
                "fecha_analisis": f"2025-11-2{i}",
                "numero_peticion": f"BIO-LIM-{i}",
                "origen": "BIO",
                "glucosa": 80.0 + i,
            }
        )

    rows_all = bioquimica.list()
    rows_lim = bioquimica.list(limit=2)

    assert len(rows_all) == 3
    assert len(rows_lim) == 2
