# tests/test_db/test_orina.py
# -*- coding: utf-8 -*-


def test_insert_and_list_orina(components):
    orina = components["orina"]

    data = {
        "fecha_analisis": "2025-11-24",
        "numero_peticion": "ORINA-001",
        "origen": "ORINA",
        "ph": 6.0,
        "densidad": 1.020,
        "glucosa": "NEG",
        "proteinas": "NEG",
        "sangre": "POS",
    }
    orina.insert(data)

    rows = orina.list()
    assert len(rows) == 1

    row = rows[0]
    assert row["fecha_analisis"] == "2025-11-24"
    assert row["numero_peticion"] == "ORINA-001"
    assert row["origen"] == "ORINA"
    assert row["ph"] == 6.0
    assert row["densidad"] == 1.020
    assert row["glucosa"] == "NEG"
    assert row["proteinas"] == "NEG"
    assert row["sangre"] == "POS"


def test_limit_in_list_orina(components):
    orina = components["orina"]

    for i in range(3):
        orina.insert(
            {
                "fecha_analisis": f"2025-11-4{i}",
                "numero_peticion": f"ORINA-LIM-{i}",
                "origen": "ORINA",
                "ph": 5.5 + 0.1 * i,
            }
        )

    rows_all = orina.list()
    rows_lim = orina.list(limit=2)

    assert len(rows_all) == 3
    assert len(rows_lim) == 2
