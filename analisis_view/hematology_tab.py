# analisis_view/hematology_tab.py
# -*- coding: utf-8 -*-

"""
Pestaña de Hematología.

- Usa BaseAnalysisTab como contenedor de tksheet.
- Carga los datos de la BD con get_rows_generic.
- Aplica coloreado de celdas fuera de rango usando compute_out_of_range_cells.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import logging

from ranges_config import RangesManager  # type: ignore
from db_manager import HematologyDB      # sólo para tipado

from .base_tab import BaseAnalysisTab
from .config import HEMA_FIELDS, HEMA_VISIBLE_FIELDS, HEMA_HEADERS
from .data_utils import get_rows_generic, compute_out_of_range_cells

logger = logging.getLogger(__name__)


class HematologyTab(BaseAnalysisTab):
    """
    Pestaña de hematología.
    """

    def __init__(
        self,
        master,
        db: Optional[HematologyDB] = None,
        ranges_manager: Optional[RangesManager] = None,
        **kwargs,
    ):
        super().__init__(master, db=db, **kwargs)

        self.ranges_manager: Optional[RangesManager] = ranges_manager
        self._rows: List[Dict[str, Any]] = []

    # ------------------------------------------------------------
    #   API específica
    # ------------------------------------------------------------
    def set_ranges_manager(self, ranges_manager: RangesManager) -> None:
        self.ranges_manager = ranges_manager

    def get_rows(self) -> List[Dict[str, Any]]:
        return self._rows

    # ------------------------------------------------------------
    #   Clear / Refresh
    # ------------------------------------------------------------
    def clear(self) -> None:
        super().clear()
        self._rows = []

    def refresh(self) -> None:
        """
        Recarga los datos de hematología desde la BD.
        """
        logger.debug("HematologyTab.refresh()")

        if self.db is None:
            self.clear()
            return

        rows = get_rows_generic(
            db=self.db,
            list_method_name="list_hematologia",
            fields_order=HEMA_FIELDS,
        )

        self._rows = rows

        if not rows:
            self.clear()
            return

        # Campos visibles (incluyen fecha_analisis, numero_peticion, origen)
        fields = HEMA_VISIBLE_FIELDS
        headers = [HEMA_HEADERS.get(f, f) for f in fields]

        data: List[List[Any]] = []
        for row in rows:
            data.append([row.get(f, "") for f in fields])

        self.sheet.set_sheet_data(
            data=data,
            reset_col_positions=True,
            reset_row_positions=True,
            redraw=True,
        )
        self.sheet.headers(headers)

        # Ajuste de anchura básica
        for i in range(len(headers)):
            if i == 0:
                self.sheet.column_width(i, 110)  # fecha
            else:
                self.sheet.column_width(i, 90)

        # Quitar resaltados previos
        try:
            self.sheet.highlight_cells(cells="all", bg=None, fg=None, redraw=False)
        except Exception:
            pass

        # Pintar fuera de rango
        if self.ranges_manager is not None:
            ranges = self.ranges_manager.get_all()
            cells = compute_out_of_range_cells(rows, fields, ranges)
            for r_idx, c_idx in cells:
                try:
                    self.sheet.highlight_cells(
                        row=r_idx,
                        column=c_idx,
                        bg="#ffdddd",
                        fg="red",
                        redraw=False,
                    )
                except Exception:
                    pass

        self.sheet.redraw()
