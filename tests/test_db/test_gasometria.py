# tests/test_db/test_gasometria.py
# -*- coding: utf-8 -*-


def test_insert_and_list_gasometria(components):
    gasometria = components["gasometria"]

    data = {
        "fecha_analisis": "2025-11-24",
        "numero_peticion": "GASO-001",
        "origen": "GAS",
        "gaso_ph": 7.40,
        "gaso_pco2": 40.0,
        "gaso_po2": 95.0,
    }
    gasometria.insert(data)

    rows = gasometria.list()
    assert len(rows) == 1

    row = rows[0]
    assert row["fecha_analisis"] == "2025-11-24"
    assert row["numero_peticion"] == "GASO-001"
    assert row["origen"] == "GAS"
    assert row["gaso_ph"] == 7.40
    assert row["gaso_pco2"] == 40.0
    assert row["gaso_po2"] == 95.0


def test_limit_in_list_gasometria(components):
    gasometria = components["gasometria"]

    for i in range(3):
        gasometria.insert(
            {
                "fecha_analisis": f"2025-11-3{i}",
                "numero_peticion": f"GASO-LIM-{i}",
                "origen": "GAS",
                "gaso_ph": 7.35 + 0.01 * i,
            }
        )

    rows_all = gasometria.list()
    rows_lim = gasometria.list(limit=2)

    assert len(rows_all) == 3
    assert len(rows_lim) == 2
