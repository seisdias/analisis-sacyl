# analisis_view/orina_tab.py
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any, Dict, List, Optional
import logging

from ranges_config import RangesManager  # type: ignore

from .base_tab import BaseAnalysisTab
from .data_utils import compute_out_of_range_cells

logger = logging.getLogger(__name__)


class OrinaTab(BaseAnalysisTab):
    """
    Pestaña Orina.

    - Oculta campos internos: id, analisis_id
    - Ordena columnas: fecha_analisis, numero_peticion, origen, (resto)
    - Resalta fuera de rango con ranges_manager (solo numéricos: ph, densidad, sodio_ur, etc.)
      Los cualitativos (NEGATIVO, +, ++) no se resaltan con el comparador actual.
    """

    META_ORDER = ["fecha_analisis", "numero_peticion", "origen"]
    HIDDEN_FIELDS = {"id", "analisis_id"}

    def __init__(
        self,
        master,
        db: Optional[Any] = None,
        ranges_manager: Optional[RangesManager] = None,
        **kwargs,
    ):
        super().__init__(master, db=db, **kwargs)
        self.ranges_manager: Optional[RangesManager] = ranges_manager
        self._rows: List[Dict[str, Any]] = []

    def set_ranges_manager(self, ranges_manager: RangesManager) -> None:
        self.ranges_manager = ranges_manager

    def get_rows(self) -> List[Dict[str, Any]]:
        return self._rows

    def clear(self) -> None:
        super().clear()
        self._rows = []

    def refresh(self) -> None:
        logger.debug("OrinaTab.refresh()")

        if self.db is None or not hasattr(self.db, "list_orina"):
            self.clear()
            return

        rows = self.db.list_orina(limit=1000)
        if not rows:
            self.clear()
            return

        first = rows[0]
        if not isinstance(first, dict):
            headers = [f"C{i}" for i in range(len(first))]
            data = [list(t) for t in rows]
            self.sheet.set_sheet_data(data=data, reset_col_positions=True, reset_row_positions=True, redraw=True)
            self.sheet.headers(headers)
            self.sheet.redraw()
            self._rows = []
            return

        self._rows = [dict(r) for r in rows]

        keys = [k for k in first.keys() if k not in self.HIDDEN_FIELDS]
        meta_fields = [k for k in self.META_ORDER if k in keys]
        other_fields = [k for k in keys if k not in meta_fields]
        fields = meta_fields + other_fields

        headers = [self._header_for(k) for k in fields]
        data: List[List[Any]] = [[r.get(f, "") for f in fields] for r in self._rows]

        self.sheet.set_sheet_data(
            data=data,
            reset_col_positions=True,
            reset_row_positions=True,
            redraw=True,
        )
        self.sheet.headers(headers)

        for i in range(len(headers)):
            self.sheet.column_width(i, 120 if fields[i] == "fecha_analisis" else 95)

        try:
            self.sheet.highlight_cells(cells="all", bg=None, fg=None, redraw=False)
        except Exception:
            pass

        if self.ranges_manager is not None:
            ranges = self.ranges_manager.get_all()
            cells = compute_out_of_range_cells(self._rows, fields, ranges)
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

    @staticmethod
    def _header_for(key: str) -> str:
        mapping = {
            "fecha_analisis": "Fecha",
            "numero_peticion": "Nº petición",
            "origen": "Origen",
            "cuerpos_cetonicos": "Cuerpos cetónicos",
            "leucocitos_ests": "Leucocitos est.",
            "urobilinogeno": "Urobilinógeno",
            "sodio_ur": "Sodio orina",
            "creatinina_ur": "Creatinina orina",
            "indice_albumina_creatinina": "Índice Alb/Cre",
            "categoria_albuminuria": "Cat. albuminuria",
            "albumina_ur": "Albúmina orina",
        }
        return mapping.get(key, key)
