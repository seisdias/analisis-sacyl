# analisis_view/view.py
# -*- coding: utf-8 -*-

"""
Vista de análisis de laboratorio usando tksheet.Sheet

- Muestra los análisis en 4 pestañas:
    • Hematología
    • Bioquímica
    • Gasometría
    • Orina
- Cada pestaña es una tabla tipo hoja de cálculo (Sheet).
- La pestaña de Hematología pinta en rojo las celdas fuera de rango
  según ranges_config.RangesManager.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from tkinter import ttk  # type: ignore
from tksheet import Sheet

from ranges_config import RangesManager
from db_manager import HematologyDB  # solo para tipado

from .config import (
    HEMA_FIELDS,
    BIOQ_FIELDS,
    ORINA_FIELDS,
    HEMA_HEADERS,
    BIOQ_HEADERS,
    ORINA_HEADERS,
)
from .data_utils import get_rows_generic, compute_out_of_range_cells

logger = logging.getLogger(__name__)


class AnalisisView(ttk.Frame):
    """
    Frame principal con un Notebook y 4 pestañas:
      - Hematología
      - Bioquímica
      - Gasometría
      - Orina
    """

    def __init__(
        self,
        master,
        db: Optional[HematologyDB] = None,
        ranges_manager: Optional[RangesManager] = None,
        **kwargs,
    ):
        super().__init__(master, **kwargs)

        self.db: Optional[HematologyDB] = db
        self.ranges_manager: Optional[RangesManager] = ranges_manager

        # Notebook con pestañas
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        # ---- Pestaña Hematología ----
        self.tab_hema = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_hema, text="Hematología")
        self.sheet_hema = self._create_sheet(self.tab_hema)

        # ---- Pestaña Bioquímica ----
        self.tab_bioq = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_bioq, text="Bioquímica")
        self.sheet_bioq = self._create_sheet(self.tab_bioq)

        # ---- Pestaña Gasometría ----
        self.tab_gaso = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_gaso, text="Gasometría")
        self.sheet_gaso = self._create_sheet(self.tab_gaso)

        # ---- Pestaña Orina ----
        self.tab_orina = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_orina, text="Orina")
        self.sheet_orina = self._create_sheet(self.tab_orina)

    # ============================================================
    #   Fabricación de Sheet
    # ============================================================
    def _create_sheet(self, parent) -> Sheet:
        sheet = Sheet(
            parent,
            data=[],
            headers=[],
            show_row_index=False,
            show_x_scrollbar=True,
            show_y_scrollbar=True,
        )
        sheet.enable_bindings(
            (
                "single_select",
                "row_select",
                "column_width_resize",
                "double_click_column_resize",
                "arrowkeys",
                "right_click_popup_menu",
                "select_all",
                "copy",
            )
        )
        sheet.pack(fill="both", expand=True)
        return sheet

    # ============================================================
    #   API pública
    # ============================================================
    def set_db(self, db: HematologyDB) -> None:
        self.db = db

    def set_ranges_manager(self, ranges_manager: RangesManager) -> None:
        self.ranges_manager = ranges_manager

    def clear(self) -> None:
        """Limpia todas las pestañas."""
        for sheet in (self.sheet_hema, self.sheet_bioq, self.sheet_gaso, self.sheet_orina):
            sheet.set_sheet_data([])
            sheet.headers([])

    def refresh(self) -> None:
        """
        Recarga los datos de la BD en todas las pestañas.
        """
        logger.debug("AnalisisView.refresh()")

        if self.db is None or not getattr(self.db, "is_open", False):
            self.clear()
            return

        self._refresh_hematologia()
        self._refresh_bioquimica()
        self._refresh_gasometria()
        self._refresh_orina()

    # ============================================================
    #   Hematología
    # ============================================================
    def _refresh_hematologia(self) -> None:
        rows = get_rows_generic(
            db=self.db,
            list_method_name="list_hematologia",
            fallback_name="list_analyses",  # compatibilidad con versiones antiguas
            fields_order=HEMA_FIELDS,
        )

        if not rows:
            self.sheet_hema.set_sheet_data([])
            self.sheet_hema.headers([])
            return

        # No mostramos el ID en la tabla
        fields = HEMA_FIELDS[1:]
        headers = [HEMA_HEADERS.get(f, f) for f in fields]

        data: List[List[Any]] = []
        for row in rows:
            data.append([row.get(f, "") for f in fields])

        self.sheet_hema.set_sheet_data(
            data=data,
            reset_col_positions=True,
            reset_row_positions=True,
            redraw=True,
        )
        self.sheet_hema.headers(headers)

        # Ajuste de anchura básica
        for i in range(len(headers)):
            if i == 0:
                self.sheet_hema.column_width(i, 110)  # fecha
            else:
                self.sheet_hema.column_width(i, 90)

        # Quitar resaltados previos
        try:
            self.sheet_hema.highlight_cells(cells="all", bg=None, fg=None, redraw=False)
        except Exception:
            # tksheet puede lanzar excepciones en algunas versiones
            pass

        # Pintar fuera de rango
        if self.ranges_manager is not None:
            ranges = self.ranges_manager.get_all()
            cells = compute_out_of_range_cells(rows, fields, ranges)
            for r_idx, c_idx in cells:
                try:
                    self.sheet_hema.highlight_cells(
                        row=r_idx,
                        column=c_idx,
                        bg="#ffdddd",
                        fg="red",
                        redraw=False,
                    )
                except Exception:
                    pass

        self.sheet_hema.redraw()

    # ============================================================
    #   Bioquímica
    # ============================================================
    def _refresh_bioquimica(self) -> None:
        if not hasattr(self.db, "list_bioquimica"):
            self.sheet_bioq.set_sheet_data([])
            self.sheet_bioq.headers([])
            return

        rows = get_rows_generic(
            db=self.db,
            list_method_name="list_bioquimica",
            fallback_name=None,
            fields_order=BIOQ_FIELDS,
        )

        if not rows:
            self.sheet_bioq.set_sheet_data([])
            self.sheet_bioq.headers([])
            return

        fields = BIOQ_FIELDS[1:]  # sin id
        headers = [BIOQ_HEADERS.get(f, f) for f in fields]

        data: List[List[Any]] = []
        for row in rows:
            data.append([row.get(f, "") for f in fields])

        self.sheet_bioq.set_sheet_data(
            data=data,
            reset_col_positions=True,
            reset_row_positions=True,
            redraw=True,
        )
        self.sheet_bioq.headers(headers)

        for i in range(len(headers)):
            if i == 0:
                self.sheet_bioq.column_width(i, 110)
            else:
                self.sheet_bioq.column_width(i, 90)

        self.sheet_bioq.redraw()

    # ============================================================
    #   Gasometría
    # ============================================================
    def _refresh_gasometria(self) -> None:
        """
        La implementación depende de si existe list_gasometria en la BD.
        Si aún no se ha creado la tabla de gasometría, se deja vacía.
        """
        if self.db is None or not hasattr(self.db, "list_gasometria"):
            self.sheet_gaso.set_sheet_data([])
            self.sheet_gaso.headers(["(No hay tabla de gasometría configurada)"])
            return

        rows = self.db.list_gasometria(limit=1000)

        if not rows:
            self.sheet_gaso.set_sheet_data([])
            self.sheet_gaso.headers([])
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

        self.sheet_gaso.set_sheet_data(
            data=data,
            reset_col_positions=True,
            reset_row_positions=True,
            redraw=True,
        )
        self.sheet_gaso.headers(headers)
        self.sheet_gaso.redraw()

    # ============================================================
    #   Orina
    # ============================================================
    def _refresh_orina(self) -> None:
        if self.db is None or not hasattr(self.db, "list_orina"):
            self.sheet_orina.set_sheet_data([])
            self.sheet_orina.headers([])
            return

        rows = get_rows_generic(
            db=self.db,
            list_method_name="list_orina",
            fallback_name=None,
            fields_order=ORINA_FIELDS,
        )

        if not rows:
            self.sheet_orina.set_sheet_data([])
            self.sheet_orina.headers([])
            return

        fields = ORINA_FIELDS[1:]  # sin id
        headers = [ORINA_HEADERS.get(f, f) for f in fields]

        data: List[List[Any]] = []
        for row in rows:
            data.append([row.get(f, "") for f in fields])

        self.sheet_orina.set_sheet_data(
            data=data,
            reset_col_positions=True,
            reset_row_positions=True,
            redraw=True,
        )
        self.sheet_orina.headers(headers)

        for i in range(len(headers)):
            if i == 0:
                self.sheet_orina.column_width(i, 110)
            else:
                self.sheet_orina.column_width(i, 90)

        self.sheet_orina.redraw()
