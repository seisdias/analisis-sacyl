# tests/test_analisis_view/test_data_utils.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from analisis_view.data_utils import (
    get_rows_generic,
    is_value_out_of_range,
    compute_out_of_range_cells,
)


class FakeDBDict:
    def __init__(self, rows):
        self._rows = rows

    def list_hematologia(self, limit: int = 1000):
        # Ignoramos limit para simplificar
        return self._rows


class FakeDBTuple:
    def __init__(self, rows):
        self._rows = rows

    def list_bioquimica(self, limit: int = 1000):
        return self._rows


@dataclass
class RangeParam:
    min_value: float | None
    max_value: float | None


def test_get_rows_generic_dict_sorted_by_fecha():
    rows = [
        {"id": 2, "fecha_extraccion": "2025-01-10", "valor": 20},
        {"id": 1, "fecha_extraccion": "2025-01-01", "valor": 10},
    ]
    db = FakeDBDict(rows)
    fields_order = ["id", "fecha_extraccion", "valor"]

    result = get_rows_generic(
        db=db,
        list_method_name="list_hematologia",
        fallback_name=None,
        fields_order=fields_order,
    )

    assert [r["id"] for r in result] == [1, 2]
    assert [r["valor"] for r in result] == [10, 20]


def test_get_rows_generic_tuples_mapping_and_len_mismatch():
    # La tercera tupla tiene longitud distinta y debe ser ignorada
    tuples = [
        (1, "2025-01-01", 10.0),
        (2, "2025-01-02", 20.0),
        (999, "2025-01-03"),  # len 2 -> se ignora
    ]
    db = FakeDBTuple(tuples)
    fields_order = ["id", "fecha_extraccion", "valor"]

    result = get_rows_generic(
        db=db,
        list_method_name="list_bioquimica",
        fallback_name=None,
        fields_order=fields_order,
    )

    assert len(result) == 2
    assert result[0]["id"] == 1
    assert result[1]["id"] == 2


def test_is_value_out_of_range_basic_cases():
    ranges: Dict[str, Any] = {
        "hemoglobina": RangeParam(min_value=12.0, max_value=18.0),
    }

    assert is_value_out_of_range("hemoglobina", "11.9", ranges) is True
    assert is_value_out_of_range("hemoglobina", "12", ranges) is False
    assert is_value_out_of_range("hemoglobina", "18", ranges) is False
    assert is_value_out_of_range("hemoglobina", "18.1", ranges) is True

    # Valores vacíos o no numéricos -> no fuera de rango
    assert is_value_out_of_range("hemoglobina", "", ranges) is False
    assert is_value_out_of_range("hemoglobina", None, ranges) is False
    assert is_value_out_of_range("hemoglobina", "abc", ranges) is False

    # Campo sin rango definido -> siempre False
    assert is_value_out_of_range("campo_inexistente", "15", ranges) is False


def test_compute_out_of_range_cells_returns_coordinates():
    rows: List[Dict[str, Any]] = [
        {"hemoglobina": "11.0", "plaquetas": "150"},
        {"hemoglobina": "13.0", "plaquetas": "50"},
    ]
    fields = ["hemoglobina", "plaquetas"]
    ranges: Dict[str, Any] = {
        "hemoglobina": RangeParam(min_value=12.0, max_value=18.0),
        "plaquetas": RangeParam(min_value=100.0, max_value=400.0),
    }

    cells = compute_out_of_range_cells(rows, fields, ranges)

    # (0, 0): hemoglobina 11.0 < 12.0
    # (1, 1): plaquetas 50 < 100
    assert (0, 0) in cells
    assert (1, 1) in cells
    # (1, 0) está dentro de rango y no debería aparecer
    assert (1, 0) not in cells
