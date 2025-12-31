# analisis_view/base_tab.py
# -*- coding: utf-8 -*-

"""
Componente base para pestañas de análisis con tksheet.Sheet.

Cada tipo de análisis (hematología, bioquímica, etc.) hereda de esta clase
y define su propia lógica de refresco y mapeo de datos.
"""

from __future__ import annotations

from typing import Any, Optional

from tkinter import ttk  # type: ignore
from tksheet import Sheet


class BaseAnalysisTab(ttk.Frame):
    """
    Pestaña base con una hoja tksheet y una referencia a la BD.

    Métodos esperados a sobreescribir:
      - refresh()
      - clear()
    """

    def __init__(self, master, db: Optional[Any] = None, **kwargs):
        super().__init__(master, **kwargs)
        self.db: Optional[Any] = db
        self.sheet: Sheet = self._create_sheet()

    # ------------------------------------------------------------
    #   Inicialización de tksheet
    # ------------------------------------------------------------
    def _create_sheet(self) -> Sheet:
        sheet = Sheet(
            self,
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

    # ------------------------------------------------------------
    #   API pública
    # ------------------------------------------------------------
    def set_db(self, db: Any) -> None:
        self.db = db

    def clear(self) -> None:
        """
        Limpia la hoja. Las subclases pueden extender este comportamiento.
        """
        self.sheet.set_sheet_data([])
        self.sheet.headers([])

    def refresh(self) -> None:
        """
        Debe ser implementado por las subclases para recargar datos desde la BD.
        """
        raise NotImplementedError("Subclasses must implement refresh()")
