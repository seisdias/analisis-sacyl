# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .defs import PARAM_DEFS


def parse_date_yyyy_mm_dd(value: Any) -> Optional[datetime]:
    txt = str(value or "").strip()
    if not txt:
        return None
    try:
        return datetime.strptime(txt, "%Y-%m-%d")
    except ValueError:
        return None


def parse_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        if isinstance(value, str):
            return float(value.replace(",", "."))
        return float(value)
    except (TypeError, ValueError):
        return None


@dataclass(frozen=True)
class SeriesPoint:
    date: datetime
    value: float


class DbSeriesProvider:
    """
    Obtiene series temporales desde la BD.
    No sabe nada de Tk ni de matplotlib.
    """

    def __init__(self, db: Any, *, param_defs: Optional[Dict[str, Dict[str, str]]] = None):
        self._db = db
        self._param_defs = param_defs or PARAM_DEFS

    def is_ready(self) -> bool:
        return self._db is not None and bool(getattr(self._db, "is_open", False))

    def get_series(self, param_name: str, *, limit: int = 1000) -> List[SeriesPoint]:
        info = self._param_defs.get(param_name)
        if not info or not self.is_ready():
            return []

        table = info.get("table")
        rows = self._list_rows_for_table(table, limit=limit)
        points: List[SeriesPoint] = []

        for r in rows:
            dt = parse_date_yyyy_mm_dd(r.get("fecha_analisis"))
            val = parse_float(r.get(param_name))
            if dt is None or val is None:
                continue
            points.append(SeriesPoint(date=dt, value=val))

        points.sort(key=lambda p: p.date)
        return points

    def _list_rows_for_table(self, table: str, *, limit: int) -> Iterable[Dict[str, Any]]:
        if table == "hematologia":
            return self._db.list_hematologia(limit=limit)
        if table == "bioquimica":
            return self._db.list_bioquimica(limit=limit)
        if table == "gasometria":
            return self._db.list_gasometria(limit=limit)
        if table == "orina":
            return self._db.list_orina(limit=limit)
        return []
