# analisis_view/gasometria_tab.py
# -*- coding: utf-8 -*-

"""
Pestaña de Gasometría.

- Usa BaseAnalysisTab como contenedor de tksheet.
- Depende directamente de db.list_gasometria(), como en la implementación original.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import logging

from .base_tab import BaseAnalysisTab

logger = logging.getLogger(__name__)


class GasometriaTab(BaseAnalysisTab):
    """
    Pestaña de gasometría.
    """

    def __init__(self, master, db: Optional[Any] = None, **kwargs):
        super().__init__(master, db=db, **kwargs)
        self._rows: List[Any] = []

    def get_rows(self) -> List[Any]:
        return self._rows

    def clear(self) -> None:
        super().clear()
        self._rows = []

    def refresh(self) -> None:
        logger.debug("GasometriaTab.refresh()")

        if self.db is None or not hasattr(self.db, "list_gasometria"):
            self.sheet.set_sheet_data([])
            self.sheet.headers(["(No hay tabla de gasometría configurada)"])
            self._rows = []
            return

        rows = self.db.list_gasometria(limit=1000)
        self._rows = rows

        if not rows:
            self.sheet.set_sheet_data([])
            self.sheet.headers([])
            return

        first = rows[0]
        if isinstance(first, dict):
            fields = [k for k in first.keys() if k != "id"]
            headers = [k for k in fields]
            data = [[r.get(f, "") for f in fields] for r in rows]
        else:
            # Si son tuplas, no sabemos el orden exacto -> mostramos tal cual
            headers = [f"C{i}" for i in range(len(first))]
            data = [list(t) for t in rows]

        self.sheet.set_sheet_data(
            data=data,
            reset_col_positions=True,
            reset_row_positions=True,
            redraw=True,
        )
        self.sheet.headers(headers)
        self.sheet.redraw()
