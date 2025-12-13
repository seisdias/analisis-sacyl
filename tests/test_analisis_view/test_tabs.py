# tests/test_analisis_view/test_tabs.py
from __future__ import annotations

from typing import Any, Dict

import pytest

from ranges_config import RangesManager

from tests.test_analisis_view.conftest import FakeDB, FakeSheet


def _make_tab_without_tk(TabCls, db=None, sheet=None, **extra_attrs):
    """
    Crea una instancia sin ejecutar __init__ (evita Tk/tksheet).
    Inyecta sheet/db y atributos que el Tab necesita.
    """
    tab = TabCls.__new__(TabCls)
    tab.db = db
    tab.sheet = sheet or FakeSheet()
    # Por si BaseAnalysisTab tiene algo más:
    for k, v in extra_attrs.items():
        setattr(tab, k, v)
    # Algunos tabs usan _rows internamente:
    if not hasattr(tab, "_rows"):
        tab._rows = []
    return tab


def test_hematology_tab_refresh_populates_and_highlights():
    from analisis_view.hematology_tab import HematologyTab

    # Valor fuera de rango: leucocitos 20 (>11)
    hema_rows = [{
        "id": 1,
        "fecha_analisis": "2025-01-10",
        "numero_peticion": "P-1",
        "origen": "Hospital",
        "leucocitos": 20.0,
        "hemoglobina": 14.0,
        "plaquetas": 200.0,
    }]

    db = FakeDB(hematologia=hema_rows)
    sheet = FakeSheet()
    rm = RangesManager()

    tab = _make_tab_without_tk(HematologyTab, db=db, sheet=sheet, ranges_manager=rm)

    tab.refresh()

    # Debe pintar datos y cabeceras
    assert sheet._data is not None
    assert sheet._headers is not None
    assert sheet.redraw_called >= 1

    # Debe haber al menos 1 highlight (fuera de rango)
    # (además del "limpiar all" si se llama)
    assert any("row" in c and "column" in c for c in sheet.highlight_calls)


def test_bioquimica_tab_hides_ids_and_shows_origen_value():
    from analisis_view.bioquimica_tab import BioquimicaTab

    rows = [{
        "id": 10,
        "analisis_id": 1,
        "glucosa": 90.0,
        "creatinina": 0.9,
        "fecha_analisis": "2025-01-10",
        "numero_peticion": "P-1",
        "origen": "Hospital",
    }]

    db = FakeDB(bioquimica=rows)
    sheet = FakeSheet()
    rm = RangesManager()

    tab = _make_tab_without_tk(BioquimicaTab, db=db, sheet=sheet, ranges_manager=rm)

    tab.refresh()

    # Cabeceras no deben incluir analisis_id ni id
    assert sheet._headers is not None
    headers_joined = " ".join(str(h) for h in sheet._headers)
    assert "analisis_id" not in headers_joined
    assert "id" not in headers_joined

    # Debe aparecer "Origen" como cabecera (según mapping del tab)
    assert any("Origen" == h or "origen" == h for h in sheet._headers)

    # La celda de origen debe venir rellena en alguna columna
    assert sheet._data is not None
    flat = [str(x) for row in sheet._data for x in row]
    assert "Hospital" in flat


def test_gasometria_tab_hides_analisis_id_and_orders_meta_first():
    from analisis_view.gasometria_tab import GasometriaTab

    rows = [{
        "id": 20,
        "analisis_id": 1,
        "fecha_analisis": "2025-01-10",
        "numero_peticion": "P-1",
        "origen": "Hospital",
        "ph_sangre": 7.41,
        "pco2": 40.0,
    }]

    db = FakeDB(gasometria=rows)
    sheet = FakeSheet()

    tab = _make_tab_without_tk(GasometriaTab, db=db, sheet=sheet)
    tab.refresh()

    # analisis_id no se muestra
    assert sheet._headers is not None
    assert "analisis_id" not in " ".join(str(h) for h in sheet._headers)

    # Meta orden: fecha_analisis, numero_peticion, origen deberían estar delante si existen
    # (en gasometria_tab usamos headers = fields)
    headers = list(sheet._headers)
    assert headers[0] in ("fecha_analisis", "Fecha")  # dependiendo de si usas mapping o crudo
