# -*- coding: utf-8 -*-
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, Dict, List, Optional

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from .api import ChartsView
from .controller import ChartsController
from .defs import PARAM_DEFS, PARAM_GROUPS


class TkChartsView(ttk.Frame):
    """
    Panel con:
      - Zona superior: checkboxes de parámetros agrupados por serie.
      - Zona inferior: área scrollable con las gráficas.
    """

    def __init__(self, master, *, db: Optional[Any] = None, ranges_manager: Optional[Any] = None, **kwargs):
        super().__init__(master, **kwargs)

        self._controller = ChartsController(db=db, ranges_manager=ranges_manager)
        self._param_vars: Dict[str, tk.BooleanVar] = {}
        self._figure_canvases: List[FigureCanvasTkAgg] = []

        # ----- Controles superiores -----
        self._controls_frame = ttk.Frame(self)
        self._controls_frame.pack(side="top", fill="x", padx=5, pady=5)
        self._build_controls()

        # ----- Área scrollable para gráficas -----
        self._canvas = tk.Canvas(self, highlightthickness=0)
        self._scrollbar = ttk.Scrollbar(self, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=self._scrollbar.set)

        self._canvas.pack(side="left", fill="both", expand=True)
        self._scrollbar.pack(side="right", fill="y")

        self._charts_frame = ttk.Frame(self._canvas)
        self._canvas_window = self._canvas.create_window((0, 0), window=self._charts_frame, anchor="nw")

        self._canvas.bind("<Configure>", self._on_canvas_configure)
        self._charts_frame.bind("<Configure>", self._on_charts_configure)

    # ---------------- API pública (ChartsView) ----------------
    def set_db(self, db: Any) -> None:
        self._controller.set_db(db)

    def set_ranges_manager(self, ranges_manager: Any) -> None:
        self._controller.set_ranges_manager(ranges_manager)

    def clear(self) -> None:
        for child in self._charts_frame.winfo_children():
            child.destroy()
        self._figure_canvases.clear()
        self._update_scrollregion()

    def refresh(self) -> None:
        if not self._controller.is_ready():
            self.clear()
            return

        selected = [name for name, var in self._param_vars.items() if var.get()]
        if not selected:
            self.clear()
            return

        self.clear()

        figs = self._controller.build_figures(selected)
        if not figs:
            self._update_scrollregion()
            return

        cols = 2
        row = 0
        col = 0

        for _param_name, fig in figs:
            chart_container = ttk.Frame(self._charts_frame)
            chart_container.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

            canvas = FigureCanvasTkAgg(fig, master=chart_container)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
            self._figure_canvases.append(canvas)

            col += 1
            if col >= cols:
                col = 0
                row += 1

        for c in range(cols):
            self._charts_frame.grid_columnconfigure(c, weight=1)

        self._update_scrollregion()

    # ---------------- UI helpers ----------------
    def _build_controls(self) -> None:
        ttk.Label(
            self._controls_frame,
            text="Parámetros a graficar:",
            font=("Segoe UI", 9, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=(0, 10), pady=(0, 5))

        current_row = 1
        for grupo, campos in PARAM_GROUPS:
            ttk.Label(
                self._controls_frame,
                text=f"{grupo}:",
                font=("Segoe UI", 9, "bold"),
            ).grid(row=current_row, column=0, sticky="w", padx=(0, 5), pady=2)

            col = 1
            for name in campos:
                if name not in PARAM_DEFS:
                    continue
                text = PARAM_DEFS[name].get("label", name)

                var = tk.BooleanVar(value=False)
                ttk.Checkbutton(
                    self._controls_frame,
                    text=text,
                    variable=var,
                    command=self._on_param_toggled,
                ).grid(row=current_row, column=col, sticky="w", padx=5, pady=2)

                self._param_vars[name] = var
                col += 1

            current_row += 1

        max_cols = max((len(campos) for _g, campos in PARAM_GROUPS), default=1) + 1
        for c in range(max_cols):
            self._controls_frame.grid_columnconfigure(c, weight=1)

    def _on_param_toggled(self) -> None:
        self.refresh()

    # ---------------- Scroll / geometry ----------------
    def _on_canvas_configure(self, event) -> None:
        self._canvas.itemconfig(self._canvas_window, width=event.width)

    def _on_charts_configure(self, _event) -> None:
        self._update_scrollregion()

    def _update_scrollregion(self) -> None:
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))
