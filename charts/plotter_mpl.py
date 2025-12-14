# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Sequence, Tuple

from matplotlib.figure import Figure
from matplotlib.dates import DateFormatter

from .series_provider import SeriesPoint


@dataclass(frozen=True)
class NormalRange:
    min_value: Optional[float]
    max_value: Optional[float]


class MatplotlibPlotter:
    """Crea Figures para una serie. No sabe nada de Tk."""

    def create_figure(
        self,
        *,
        title: str,
        points: Sequence[SeriesPoint],
        normal_range: Optional[NormalRange] = None,
        figsize: Tuple[float, float] = (4.5, 2.7),
        dpi: int = 100,
    ) -> Figure:
        fig = Figure(figsize=figsize, dpi=dpi)
        ax = fig.add_subplot(111)

        fechas = [p.date for p in points]
        valores = [p.value for p in points]

        # Evita warning marker duplicado
        ax.plot(fechas, valores, marker="o", linestyle="-")

        ax.xaxis.set_major_formatter(DateFormatter("%Y-%m-%d"))
        for label in ax.get_xticklabels():
            label.set_rotation(45)
            label.set_ha("right")
            label.set_fontsize(8)

        ax.set_title(title, fontsize=10)
        ax.set_ylabel("Valor")

        if normal_range and (normal_range.min_value is not None or normal_range.max_value is not None):
            ymin_plot = min(valores)
            ymax_plot = max(valores)
            ymin = normal_range.min_value if normal_range.min_value is not None else ymin_plot
            ymax = normal_range.max_value if normal_range.max_value is not None else ymax_plot
            ax.axhspan(ymin, ymax, alpha=0.15)

        ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.6)
        return fig
