# analisis_view/data_utils.py
# -*- coding: utf-8 -*-

"""
Funciones auxiliares para la vista de análisis:

- Normalización de filas devueltas por la BD a dicts.
- Ordenación por fecha de extracción.
- Cálculo de celdas fuera de rango a partir de RangesManager.

Este módulo NO depende de Tkinter ni de tksheet, para poder testearlo
fácilmente con pytest.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence


def get_rows_generic(
    db: Any,
    list_method_name: str,
    fields_order: List[str],
    limit: int = 1000,
) -> List[Dict[str, Any]]:
    """
    Llama a db.<list_method_name>(limit=...) o al fallback si existe,
    y convierte las filas a dicts con las claves de fields_order.

    Ordena el resultado por fecha_extraccion (o fecha_analisis) si existe.
    """

    if db is None:
        return []

    method = getattr(db, list_method_name, None)

    if method is None:
        return []

    tuples_or_dicts = method(limit=limit)
    if not tuples_or_dicts:
        return []

    rows: List[Dict[str, Any]] = []
    first = tuples_or_dicts[0]

    if isinstance(first, dict):
        # Ya vienen como dicts: copiamos por seguridad
        for r in tuples_or_dicts:
            rows.append(dict(r))
    else:
        # Tuplas: las mapeamos usando fields_order
        for t in tuples_or_dicts:
            if not isinstance(t, Sequence):
                continue
            if len(t) != len(fields_order):
                # Si el len no coincide, se ignora la fila
                continue
            row = {field: value for field, value in zip(fields_order, t)}
            rows.append(row)

    rows.sort(key=_parse_fecha_extraccion)
    return rows


def _parse_fecha_extraccion(r: Dict[str, Any]) -> datetime:
    """
    Intenta obtener una fecha a partir de 'fecha_extraccion' o 'fecha_analisis'.
    Si no puede, devuelve datetime.min para ir al principio.
    """
    value = r.get("fecha_extraccion") or r.get("fecha_analisis") or ""
    if not value:
        return datetime.min

    # Se asume formato 'YYYY-MM-DD' (como en db_manager)
    try:
        return datetime.strptime(str(value), "%Y-%m-%d")
    except ValueError:
        return datetime.min


def is_value_out_of_range(
    field_name: str,
    value: Any,
    ranges: Dict[str, Any],
) -> bool:
    """
    Devuelve True si value está fuera de rango para field_name.

    Se espera que 'ranges' sea lo que devuelve RangesManager.get_all(), es decir,
    un dict { nombre_parametro: objeto_con_min_y_max } donde cada objeto tiene
    atributos 'min_value' y 'max_value'.
    """
    param = ranges.get(field_name)
    if not param:
        return False

    # Intentar convertir a float
    try:
        text = str(value).strip()
        if text == "":
            return False
        val = float(text.replace(",", "."))
    except (TypeError, ValueError):
        return False

    min_v = getattr(param, "min_value", None)
    max_v = getattr(param, "max_value", None)

    if min_v is not None and val < min_v:
        return True
    if max_v is not None and val > max_v:
        return True
    return False


def compute_out_of_range_cells(
    rows: List[Dict[str, Any]],
    fields: List[str],
    ranges: Dict[str, Any],
) -> List[tuple[int, int]]:
    """
    Recorre las filas y devuelve una lista de coordenadas (row_idx, col_idx)
    de aquellas celdas cuyo valor está fuera de los rangos definidos.

    Esta función NO aplica ningún coloreado; sólo calcula qué celdas destacar.
    """
    out_of_range_cells: List[tuple[int, int]] = []

    if not ranges:
        return out_of_range_cells

    for r_idx, row in enumerate(rows):
        for c_idx, field_name in enumerate(fields):
            if field_name not in ranges:
                continue

            value = row.get(field_name)
            if is_value_out_of_range(field_name, value, ranges):
                out_of_range_cells.append((r_idx, c_idx))

    return out_of_range_cells
