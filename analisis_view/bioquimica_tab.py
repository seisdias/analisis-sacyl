# analisis_view/bioquimica_tab.py
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any, Dict, List, Optional
import logging

from ranges_config import RangesManager  # type: ignore

from .base_tab import BaseAnalysisTab
from .data_utils import compute_out_of_range_cells

logger = logging.getLogger(__name__)


class BioquimicaTab(BaseAnalysisTab):
    """
    Pestaña Bioquímica.

    - Oculta campos internos: id, analisis_id
    - Ordena columnas: fecha_analisis, numero_peticion, origen, (resto)
    - Resalta fuera de rango con ranges_manager (solo valores numéricos)
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
        logger.debug("BioquimicaTab.refresh()")

        if self.db is None or not hasattr(self.db, "list_bioquimica"):
            self.clear()
            return

        rows = self.db.list_bioquimica(limit=1000)
        if not rows:
            self.clear()
            return

        # Normalizamos a dicts (por si acaso)
        first = rows[0]
        if not isinstance(first, dict):
            # Si vinieran tuplas, mostramos tal cual
            headers = [f"C{i}" for i in range(len(first))]
            data = [list(t) for t in rows]
            self.sheet.set_sheet_data(data=data, reset_col_positions=True, reset_row_positions=True, redraw=True)
            self.sheet.headers(headers)
            self.sheet.redraw()
            self._rows = []
            return

        self._rows = [dict(r) for r in rows]

        # Campos visibles (ordenados)
        keys = [k for k in first.keys() if k not in self.HIDDEN_FIELDS]
        meta_fields = [k for k in self.META_ORDER if k in keys]
        other_fields = [k for k in keys if k not in meta_fields]
        fields = meta_fields + other_fields

        headers = [self._header_for(k) for k in fields]
        data: List[List[Any]] = []
        for r in self._rows:
            row_values: List[Any] = []
            for f in fields:
                if f == "origen":
                    val = r.get("origen") or ""
                    if val == "" and "analisis_id" in r:
                        val = self._get_origen_from_analisis(r.get("analisis_id")) or ""
                    row_values.append(val)
                else:
                    row_values.append(r.get(f, ""))
            data.append(row_values)

        self.sheet.set_sheet_data(
            data=data,
            reset_col_positions=True,
            reset_row_positions=True,
            redraw=True,
        )
        self.sheet.headers(headers)

        # Ajuste de anchura: fecha un poco más grande
        for i in range(len(headers)):
            self.sheet.column_width(i, 120 if fields[i] == "fecha_analisis" else 95)

        # limpiar highlights previos
        try:
            self.sheet.highlight_cells(cells="all", bg=None, fg=None, redraw=False)
        except Exception:
            pass

        # aplicar fuera de rango
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
        # Cabeceras mínimas legibles sin depender de config.py
        mapping = {
            "fecha_analisis": "Fecha",
            "numero_peticion": "Nº petición",
            "origen": "Origen",
            "colesterol_total": "Colesterol total",
            "colesterol_hdl": "Colesterol HDL",
            "colesterol_ldl": "Colesterol LDL",
            "colesterol_no_hdl": "Colesterol no HDL",
            "indice_riesgo": "Índice riesgo",
            "vitamina_b12": "Vitamina B12",
        }
        return mapping.get(key, key)

    def _get_origen_from_analisis(self, analisis_id: Any) -> Optional[str]:
        """
        Intenta recuperar el origen desde la tabla/entidad 'analisis' usando analisis_id.
        Si el DB no soporta el método, devuelve None.
        """
        if analisis_id is None or self.db is None:
            return None

        # Nombres de métodos que podríamos tener (según evolucione db_manager)
        for method_name in ("get_analisis_by_id", "get_analisis", "get_analysis_by_id", "get_analysis"):
            method = getattr(self.db, method_name, None)
            if callable(method):
                try:
                    a = method(analisis_id)
                    if isinstance(a, dict):
                        return a.get("origen") or None
                except Exception:
                    return None
        return None



