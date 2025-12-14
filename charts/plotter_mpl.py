# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

from matplotlib.figure import Figure
from matplotlib.dates import AutoDateLocator, ConciseDateFormatter

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

        ax.plot(fechas, valores, marker="o", linestyle="-")

        # --- Fechas: locator automático + formato compacto ---
        locator = AutoDateLocator(minticks=3, maxticks=7)
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(ConciseDateFormatter(locator))

        # Ajuste automático de rotación/espaciado
        fig.autofmt_xdate(rotation=30, ha="right")

        ax.set_title(title, fontsize=10)
        ax.set_ylabel("Valor")

        if normal_range and (normal_range.min_value is not None or normal_range.max_value is not None):
            ymin_plot = min(valores)
            ymax_plot = max(valores)
            ymin = normal_range.min_value if normal_range.min_value is not None else ymin_plot
            ymax = normal_range.max_value if normal_range.max_value is not None else ymax_plot
            ax.axhspan(ymin, ymax, alpha=0.15)

        ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.6)

        # Evita cortes de etiquetas en canvas pequeño
        fig.tight_layout()

        return fig
