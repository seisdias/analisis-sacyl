# analisis_view/bioquimica_tab.py
# -*- coding: utf-8 -*-

"""
Pestaña de Bioquímica.

- Usa BaseAnalysisTab como contenedor de tksheet.
- Carga los datos de la BD con get_rows_generic.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import logging

from .base_tab import BaseAnalysisTab
from .config import BIOQ_FIELDS, BIOQ_VISIBLE_FIELDS, BIOQ_HEADERS
from .data_utils import get_rows_generic

logger = logging.getLogger(__name__)


class BioquimicaTab(BaseAnalysisTab):
    """
    Pestaña de bioquímica.
    """

    def __init__(self, master, db: Optional[Any] = None, **kwargs):
        super().__init__(master, db=db, **kwargs)
        self._rows: List[Dict[str, Any]] = []

    def get_rows(self) -> List[Dict[str, Any]]:
        return self._rows

    def clear(self) -> None:
        super().clear()
        self._rows = []

    def refresh(self) -> None:
        logger.debug("BioquimicaTab.refresh()")

        if self.db is None or not hasattr(self.db, "list_bioquimica"):
            self.clear()
            return

        rows = get_rows_generic(
            db=self.db,
            list_method_name="list_bioquimica",
            fallback_name=None,
            fields_order=BIOQ_FIELDS,
        )

        self._rows = rows

        if not rows:
            self.clear()
            return

        fields = BIOQ_VISIBLE_FIELDS
        headers = [BIOQ_HEADERS.get(f, f) for f in fields]

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

        for i in range(len(headers)):
            if i == 0:
                self.sheet.column_width(i, 110)
            else:
                self.sheet.column_width(i, 90)

        self.sheet.redraw()
