# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

from .defs import PARAM_DEFS
from .plotter_mpl import MatplotlibPlotter, NormalRange
from .series_provider import DbSeriesProvider, SeriesPoint


class ChartsController:
    """
    Orquesta:
      - params seleccionados
      - obtención series en provider
      - creación Figures en plotter
    No sabe nada de Tk.
    """

    def __init__(
        self,
        *,
        db: Any = None,
        ranges_manager: Any = None,
        provider: Optional[DbSeriesProvider] = None,
        plotter: Optional[MatplotlibPlotter] = None,
        param_defs: Optional[Dict[str, Dict[str, str]]] = None,
    ):
        self._db = db
        self._ranges_manager = ranges_manager
        self._param_defs = param_defs or PARAM_DEFS
        self._provider = provider or DbSeriesProvider(db, param_defs=self._param_defs)
        self._plotter = plotter or MatplotlibPlotter()

    def set_db(self, db: Any) -> None:
        self._db = db
        self._provider = DbSeriesProvider(db, param_defs=self._param_defs)

    def set_ranges_manager(self, ranges_manager: Any) -> None:
        self._ranges_manager = ranges_manager

    def is_ready(self) -> bool:
        return self._provider.is_ready()

    def build_figures(self, selected_params: Sequence[str]) -> List[Tuple[str, Any]]:
        """
        Devuelve lista de (param_name, Figure) para los parámetros seleccionados
        que tengan datos.
        """
        if not self.is_ready() or not selected_params:
            return []

        result: List[Tuple[str, Any]] = []
        for param_name in selected_params:
            points = self._provider.get_series(param_name)
            if not points:
                continue

            title = self._param_defs.get(param_name, {}).get("label", param_name)
            normal_range = self._get_normal_range(param_name)

            fig = self._plotter.create_figure(
                title=title,
                points=points,
                normal_range=normal_range,
            )
            result.append((param_name, fig))

        return result

    def _get_normal_range(self, param_name: str) -> Optional[NormalRange]:
        if self._ranges_manager is None:
            return None
        try:
            pr = self._ranges_manager.get_all().get(param_name)
        except Exception:
            return None
        if not pr:
            return None
        return NormalRange(getattr(pr, "min_value", None), getattr(pr, "max_value", None))
