# -*- coding: utf-8 -*-
"""
Panel de gráficas para análisis de hematología.

Requisitos:
    pip install matplotlib

Este panel:
- Muestra checkboxes para elegir qué parámetros graficar.
- Dibuja una gráfica por parámetro seleccionado (valor vs fecha).
- Sombrea el rango válido según ranges_config.RangesManager.
- Se usa como panel inferior en la ventana principal, debajo de AnalisisView.
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from db_manager import HematologyDB
from ranges_config import RangesManager

logger = logging.getLogger(__name__)


class ChartsView(ttk.Frame):
    """
    Panel inferior que muestra gráficas de evolución de parámetros.

    - Selección de parámetros mediante checkbuttons.
    - Gráficas incrustadas en un frame con scroll vertical.
    """

    DATE_FIELD_DB = "fecha_extraccion"

    # Reutilizamos la misma lógica de agrupación que en AnalisisView
    CATEGORIES = {
        "Hemograma básico": [
            ("leucocitos", "Leucocitos"),
            ("hematies", "Hematíes"),
            ("hemoglobina", "Hemoglobina"),
            ("hematocrito", "Hematocrito"),
            ("vcm", "VCM"),
            ("hcm", "HCM"),
            ("chcm", "CHCM"),
            ("rdw", "RDW"),
            ("plaquetas", "Plaquetas"),
        ],
        "Fórmula leucocitaria": [
            ("neutrofilos_pct", "Neutrófilos (%)"),
            ("linfocitos_pct", "Linfocitos (%)"),
            ("monocitos_pct", "Monocitos (%)"),
            ("eosinofilos_pct", "Eosinófilos (%)"),
            ("basofilos_pct", "Basófilos (%)"),
            ("neutrofilos_abs", "Neutrófilos (abs)"),
            ("linfocitos_abs", "Linfocitos (abs)"),
            ("monocitos_abs", "Monocitos (abs)"),
            ("eosinofilos_abs", "Eosinófilos (abs)"),
            ("basofilos_abs", "Basófilos (abs)"),
        ],
        "Serie plaquetar": [
            ("vpm", "VPM"),
        ],
    }

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

        # Cache de filas (mismo formato que list_analyses + mapeo)
        self._rows_cache: List[Dict[str, Any]] = []

        # Campos seleccionados para graficar
        self._selected_params: Dict[str, tk.BooleanVar] = {}

        # ====== PARTE SUPERIOR: SELECTORES ======
        selectors_frame = ttk.LabelFrame(self, text="Gráficas a mostrar")
        selectors_frame.pack(side="top", fill="x", padx=5, pady=5)

        # Creamos una fila horizontal por categoría
        self._selected_params = {}
        row = 0
        for cat_name, fields in self.CATEGORIES.items():
            row_frame = ttk.Frame(selectors_frame)
            row_frame.grid(row=row, column=0, sticky="w", pady=2)

            # Etiqueta de la categoría al inicio de la fila
            ttk.Label(
                row_frame,
                text=f"{cat_name}:",
                font=("Segoe UI", 9, "bold")
            ).pack(side="left", padx=(0, 8))

            # Checkbuttons de los parámetros en horizontal
            for field_name, label in fields:
                var = tk.BooleanVar(value=False)  # inicialmente no se grafica
                chk = ttk.Checkbutton(
                    row_frame,
                    text=label,
                    variable=var,
                    command=self.refresh,
                )
                chk.pack(side="left", padx=3, pady=1)
                self._selected_params[field_name] = var

            row += 1


        # ====== PARTE INFERIOR: SCROLL + FRAME DE GRÁFICAS ======
        scroll_container = ttk.Frame(self)
        scroll_container.pack(fill="both", expand=True, padx=5, pady=(0, 5))

        self.canvas = tk.Canvas(scroll_container, highlightthickness=0)
        self.vscroll = ttk.Scrollbar(
            scroll_container, orient="vertical", command=self.canvas.yview
        )
        self.canvas.configure(yscrollcommand=self.vscroll.set)

        self.plots_frame = ttk.Frame(self.canvas)

        # Embebemos plots_frame dentro del canvas
        self.canvas.create_window((0, 0), window=self.plots_frame, anchor="nw")

        self.canvas.pack(side="left", fill="both", expand=True)
        self.vscroll.pack(side="right", fill="y")

        # Ajustar región de scroll cuando cambie el tamaño interno
        self.plots_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        # Ajustar ancho del frame interno al ancho del canvas
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfigure(
                1, width=e.width  # el primer (y único) window item
            ),
        )

        # Label por defecto si no hay gráficas
        self._no_charts_label = ttk.Label(
            self.plots_frame,
            text="Selecciona uno o varios parámetros arriba para ver sus gráficas.",
            justify="center",
        )
        self._no_charts_label.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Referencias a canvases de matplotlib para poder destruirlos
        self._figure_canvases: List[FigureCanvasTkAgg] = []

    # ========= API PÚBLICA =========
    def set_db(self, db: HematologyDB):
        self.db = db

    def set_ranges_manager(self, ranges_manager: RangesManager):
        self.ranges_manager = ranges_manager
        self.refresh()

    def clear(self):
        """Limpia gráficas y datos."""
        self._rows_cache = []
        self._clear_plots()
        self._show_no_charts_label()

    def refresh(self):
        """
        Vuelve a leer los datos de la BD y reconstruye las gráficas
        según los parámetros seleccionados.
        """
        logger.debug("ChartsView.refresh() llamado")

        if self.db is None or not getattr(self.db, "is_open", False):
            logger.debug("ChartsView: no hay BD abierta")
            self.clear()
            return

        if not hasattr(self.db, "list_analyses"):
            logger.debug("ChartsView: db no tiene list_analyses")
            self.clear()
            return

        tuples = self.db.list_analyses(limit=1000)

        # Importamos el orden de campos desde HematologyDB
        from db_manager import HematologyDB as HDB

        fields_order = HDB.DB_FIELDS_ORDER  # o usa la constante que tengas
        self._rows_cache = []

        for t in tuples:
            if len(t) != len(fields_order):
                continue
            row = {field: value for field, value in zip(fields_order, t)}
            self._rows_cache.append(row)

        # Ordenar por fecha
        def parse_fecha(r: Dict[str, Any]):
            value = r.get(self.DATE_FIELD_DB, "")
            if not value:
                return datetime.min
            try:
                return datetime.strptime(str(value), "%Y-%m-%d")
            except ValueError:
                return datetime.min

        self._rows_cache.sort(key=parse_fecha)

        # Construir gráficas
        self._rebuild_plots()

    # ========= INTERNO: GESTIÓN DE GRÁFICAS =========
    def _clear_plots(self):
        """Elimina todas las figuras de matplotlib del frame."""
        for fc in self._figure_canvases:
            fc.get_tk_widget().destroy()
        self._figure_canvases.clear()

        for widget in self.plots_frame.winfo_children():
            widget.destroy()

    def _show_no_charts_label(self):
        self._no_charts_label = ttk.Label(
            self.plots_frame,
            text="Selecciona uno o varios parámetros arriba para ver sus gráficas.",
            justify="center",
        )
        self._no_charts_label.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    def _rebuild_plots(self):
        """Reconstruye las gráficas según los parámetros seleccionados."""
        self._clear_plots()

        if not self._rows_cache:
            self._show_no_charts_label()
            return

        # Campos seleccionados
        selected_fields = [
            f for f, var in self._selected_params.items() if var.get()
        ]

        if not selected_fields:
            self._show_no_charts_label()
            return

        # Para mostrar cabeceras legibles
        field_to_label: Dict[str, str] = {}
        for _cat, fields in self.CATEGORIES.items():
            for f, lbl in fields:
                field_to_label[f] = lbl

        # Colores para las gráficas (ciclo)
        colors = [
            "tab:blue",
            "tab:orange",
            "tab:green",
            "tab:red",
            "tab:purple",
            "tab:brown",
            "tab:pink",
            "tab:gray",
            "tab:olive",
            "tab:cyan",
        ]

        # Disposición en cuadrícula: 2 columnas
        cols = 2

        for idx, field in enumerate(selected_fields):
            row = idx // cols
            col = idx % cols

            fig = Figure(figsize=(4, 2.5), dpi=100)
            ax = fig.add_subplot(111)

            xs: List[datetime] = []
            ys: List[float] = []

            for r in self._rows_cache:
                fecha_str = r.get(self.DATE_FIELD_DB)
                valor = r.get(field)

                try:
                    dt = datetime.strptime(str(fecha_str), "%Y-%m-%d")
                except Exception:
                    continue

                try:
                    text = str(valor).strip()
                    if text == "":
                        continue
                    val = float(text.replace(",", "."))
                except Exception:
                    continue

                xs.append(dt)
                ys.append(val)

            if xs and ys:
                color = colors[idx % len(colors)]
                ax.plot(xs, ys, marker="o", color=color)
                ax.tick_params(axis="x", rotation=45)
            else:
                ax.text(
                    0.5,
                    0.5,
                    "Sin datos",
                    transform=ax.transAxes,
                    ha="center",
                    va="center",
                )

            # Título de la gráfica
            ax.set_title(field_to_label.get(field, field))

            # Banda de rango válido
            if self.ranges_manager is not None:
                param = self.ranges_manager.get_all().get(field)
                if param is not None:
                    min_v = param.min_value
                    max_v = param.max_value
                    if min_v is not None and max_v is not None:
                        ax.axhspan(min_v, max_v, color="green", alpha=0.1)
                    elif min_v is not None:
                        ax.axhline(min_v, color="green", linestyle="--", alpha=0.5)
                    elif max_v is not None:
                        ax.axhline(max_v, color="green", linestyle="--", alpha=0.5)

            ax.set_xlabel("Fecha")
            ax.set_ylabel("Valor")

            canvas = FigureCanvasTkAgg(fig, master=self.plots_frame)
            widget = canvas.get_tk_widget()
            widget.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)

            canvas.draw()
            self._figure_canvases.append(canvas)

        # Hacer que las celdas de la rejilla se expandan
        max_row = (len(selected_fields) - 1) // cols
        for r in range(max_row + 1):
            self.plots_frame.rowconfigure(r, weight=1)
        for c in range(cols):
            self.plots_frame.columnconfigure(c, weight=1)
