# analisis_view/hematology_tab.py
# -*- coding: utf-8 -*-

"""
Pestaña de Hematología.

- Usa BaseAnalysisTab como contenedor de tksheet.
- Carga los datos de la BD con get_rows_generic.
- Aplica coloreado de celdas fuera de rango usando compute_out_of_range_cells.
- Notifica cambios de selección a un callback de metadatos (para el panel fijo).
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional
import logging

from ranges_config import RangesManager  # type: ignore
from db_manager import HematologyDB      # sólo para tipado

from .base_tab import BaseAnalysisTab
from .config import HEMA_FIELDS, HEMA_VISIBLE_FIELDS, HEMA_HEADERS
from .data_utils import get_rows_generic, compute_out_of_range_cells

logger = logging.getLogger(__name__)

MetadataCallback = Callable[[Dict[str, Any]], None]


class HematologyTab(BaseAnalysisTab):
    """
    Pestaña de hematología.

    Opcionalmente recibe:
      - ranges_manager: para colorear fuera de rango.
      - metadata_callback: para actualizar el panel de metadatos
        (fecha, nº de petición, origen) en AnalisisView.
    """

    def __init__(
        self,
        master,
        db: Optional[HematologyDB] = None,
        ranges_manager: Optional[RangesManager] = None,
        metadata_callback: Optional[MetadataCallback] = None,
        **kwargs,
    ):
        super().__init__(master, db=db, **kwargs)

        self.ranges_manager: Optional[RangesManager] = ranges_manager
        self.metadata_callback: Optional[MetadataCallback] = metadata_callback
        self._rows: List[Dict[str, Any]] = []

        # Binding para actualizar metadatos al seleccionar una celda
        self.sheet.extra_bindings(
            [
                ("cell_select", self._on_cell_select),
            ]
        )

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
            fallback_name="list_analyses",  # compatibilidad con versiones antiguas
            fields_order=HEMA_FIELDS,
        )

        self._rows = rows

        if not rows:
            self.clear()
            return

        # Sólo los campos visibles (sin id, sin origen)
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

        # Actualizar metadatos con el último análisis (más reciente)
        if rows and self.metadata_callback is not None:
            self.metadata_callback(rows[-1])

    # ------------------------------------------------------------
    #   Eventos
    # ------------------------------------------------------------
    def _on_cell_select(self, event: Any) -> None:
        """
        Callback al seleccionar una celda en la hoja de hematología.
        Notifica al callback de metadatos la fila seleccionada.
        """
        if not self._rows or self.metadata_callback is None:
            return

        try:
            r, c = self.sheet.get_currently_selected()
        except Exception:
            return

        if isinstance(r, int) and 0 <= r < len(self._rows):
            row = self._rows[r]
            self.metadata_callback(row)
