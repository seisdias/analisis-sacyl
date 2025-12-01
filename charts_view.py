# -*- coding: utf-8 -*-
"""
Panel de gráficas de evolución de parámetros de laboratorio.

Soporta:
 - Hematología (tabla hematologia)
 - Bioquímica (tabla bioquimica)
 - Gasometría (tabla gasometria)
 - Orina cuantitativa (tabla orina)

Cada parámetro:
 - Tiene un checkbox para mostrar/ocultar su gráfica.
 - Se obtiene de la tabla correspondiente.
 - Si existe rango en RangesManager (hematología), se sombrea el rango normal.

Autor: Borja Alonso Tristán
Año: 2025
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime
from typing import Dict, Any, List, Optional

import matplotlib
matplotlib.use("TkAgg")

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.dates import DateFormatter

from db_manager import HematologyDB
from ranges_config import RangesManager, ParamRange


class ChartsView(ttk.Frame):
    """
    Panel con:
      - Zona superior: checkboxes de parámetros agrupados por serie.
      - Zona inferior: área scrollable con las gráficas.
    """

    # ------------------------------------------------------------------
    #   DEFINICIÓN DE PARÁMETROS
    #   key == nombre de campo en BD cuando sea numérico único
    # ------------------------------------------------------------------
    # Mapa: nombre_parametro -> (tabla, etiqueta)
    PARAM_DEFS: Dict[str, Dict[str, str]] = {
        # ---- HEMATOLOGÍA (tabla hematologia) ----
        "leucocitos":        {"table": "hematologia", "label": "Leucocitos"},
        "neutrofilos_pct":   {"table": "hematologia", "label": "Neutrófilos (%)"},
        "linfocitos_pct":    {"table": "hematologia", "label": "Linfocitos (%)"},
        "monocitos_pct":     {"table": "hematologia", "label": "Monocitos (%)"},
        "eosinofilos_pct":   {"table": "hematologia", "label": "Eosinófilos (%)"},
        "basofilos_pct":     {"table": "hematologia", "label": "Basófilos (%)"},
        "neutrofilos_abs":   {"table": "hematologia", "label": "Neutrófilos (abs)"},
        "linfocitos_abs":    {"table": "hematologia", "label": "Linfocitos (abs)"},
        "monocitos_abs":     {"table": "hematologia", "label": "Monocitos (abs)"},
        "eosinofilos_abs":   {"table": "hematologia", "label": "Eosinófilos (abs)"},
        "basofilos_abs":     {"table": "hematologia", "label": "Basófilos (abs)"},
        "hematies":          {"table": "hematologia", "label": "Hematíes"},
        "hemoglobina":       {"table": "hematologia", "label": "Hemoglobina"},
        "hematocrito":       {"table": "hematologia", "label": "Hematocrito"},
        "vcm":               {"table": "hematologia", "label": "VCM"},
        "hcm":               {"table": "hematologia", "label": "HCM"},
        "chcm":              {"table": "hematologia", "label": "CHCM"},
        "rdw":               {"table": "hematologia", "label": "RDW"},
        "plaquetas":         {"table": "hematologia", "label": "Plaquetas"},
        "vpm":               {"table": "hematologia", "label": "VPM"},

        # ---- BIOQUÍMICA (tabla bioquimica) ----
        "glucosa":                   {"table": "bioquimica", "label": "Glucosa"},
        "urea":                      {"table": "bioquimica", "label": "Urea"},
        "creatinina":                {"table": "bioquimica", "label": "Creatinina"},
        "sodio":                     {"table": "bioquimica", "label": "Sodio"},
        "potasio":                   {"table": "bioquimica", "label": "Potasio"},
        "cloro":                     {"table": "bioquimica", "label": "Cloro"},
        "calcio":                    {"table": "bioquimica", "label": "Calcio"},
        "fosforo":                   {"table": "bioquimica", "label": "Fósforo"},
        "colesterol_total":          {"table": "bioquimica", "label": "Colesterol total"},
        "colesterol_hdl":            {"table": "bioquimica", "label": "Colesterol HDL"},
        "colesterol_ldl":            {"table": "bioquimica", "label": "Colesterol LDL"},
        "colesterol_no_hdl":         {"table": "bioquimica", "label": "Colesterol no HDL"},
        "trigliceridos":             {"table": "bioquimica", "label": "Triglicéridos"},
        "indice_riesgo":             {"table": "bioquimica", "label": "Índice de riesgo"},
        "hierro":                    {"table": "bioquimica", "label": "Hierro"},
        "ferritina":                 {"table": "bioquimica", "label": "Ferritina"},
        "vitamina_b12":              {"table": "bioquimica", "label": "Vitamina B12"},

        # ---- GASOMETRÍA (tabla gasometria) ----
        "gaso_ph":                   {"table": "gasometria", "label": "pH (gaso)"},
        "gaso_pco2":                 {"table": "gasometria", "label": "pCO₂"},
        "gaso_po2":                  {"table": "gasometria", "label": "pO₂"},
        "gaso_tco2":                 {"table": "gasometria", "label": "CO₂ total (TCO₂)"},
        "gaso_so2_calc":             {"table": "gasometria", "label": "sO₂ calc."},
        "gaso_so2":                  {"table": "gasometria", "label": "sO₂ medida"},
        "gaso_p50":                  {"table": "gasometria", "label": "p50"},
        "gaso_bicarbonato":         {"table": "gasometria", "label": "Bicarbonato"},
        "gaso_sbc":                  {"table": "gasometria", "label": "Bicarbonato estándar (SBC)"},
        "gaso_eb":                   {"table": "gasometria", "label": "Exceso de bases (EB)"},
        "gaso_beecf":                {"table": "gasometria", "label": "Exceso bases ECF (BEecf)"},
        "gaso_lactato":              {"table": "gasometria", "label": "Lactato"},

        # ---- ORINA CUANTITATIVA (tabla orina) ----
        "ph":                        {"table": "orina", "label": "pH orina"},
        "densidad":                  {"table": "orina", "label": "Densidad orina"},
        "sodio_ur":                  {"table": "orina", "label": "Sodio orina"},
        "creatinina_ur":             {"table": "orina", "label": "Creatinina orina"},
        "indice_albumina_creatinina":{"table": "orina", "label": "Índice Alb/Cre"},
        "albumina_ur":               {"table": "orina", "label": "Albúmina orina"},
    }

    # Grupos para organizar checkboxes
    PARAM_GROUPS = [
        (
            "Hemograma",
            [
                "leucocitos",
                "hematies",
                "hemoglobina",
                "hematocrito",
                "vcm",
                "hcm",
                "chcm",
                "rdw",
                "plaquetas",
                "vpm",
                "neutrofilos_pct",
                "linfocitos_pct",
                "monocitos_pct",
                "eosinofilos_pct",
                "basofilos_pct",
                "neutrofilos_abs",
                "linfocitos_abs",
                "monocitos_abs",
                "eosinofilos_abs",
                "basofilos_abs",
            ],
        ),
        (
            "Bioquímica",
            [
                "glucosa",
                "urea",
                "creatinina",
                "sodio",
                "potasio",
                "cloro",
                "calcio",
                "fosforo",
                "colesterol_total",
                "colesterol_hdl",
                "colesterol_ldl",
                "colesterol_no_hdl",
                "trigliceridos",
                "indice_riesgo",
                "hierro",
                "ferritina",
                "vitamina_b12",
            ],
        ),
        (
            "Gasometría",
            [
                "gaso_ph",
                "gaso_pco2",
                "gaso_po2",
                "gaso_tco2",
                "gaso_so2_calc",
                "gaso_so2",
                "gaso_p50",
                "gaso_bicarbonato",
                "gaso_sbc",
                "gaso_eb",
                "gaso_beecf",
                "gaso_lactato",
            ],
        ),
        (
            "Orina cuantitativa",
            [
                "ph",
                "densidad",
                "sodio_ur",
                "creatinina_ur",
                "indice_albumina_creatinina",
                "albumina_ur",
            ],
        ),
    ]

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

        # nombre_parametro -> BooleanVar
        self.param_vars: Dict[str, tk.BooleanVar] = {}

        # Para evitar GC de figuras
        self._figure_canvases: List[FigureCanvasTkAgg] = []

        # ----- Controles superiores -----
        self.controls_frame = ttk.Frame(self)
        self.controls_frame.pack(side="top", fill="x", padx=5, pady=5)
        self._build_controls()

        # ----- Área scrollable para gráficas -----
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.charts_frame = ttk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.charts_frame, anchor="nw"
        )

        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.charts_frame.bind("<Configure>", self._on_charts_configure)

    # ==========================================================
    #   API pública
    # ==========================================================
    def set_db(self, db: Optional[HematologyDB]):
        self.db = db

    def set_ranges_manager(self, ranges_manager: RangesManager):
        self.ranges_manager = ranges_manager

    def clear(self):
        """Elimina todas las gráficas."""
        for child in self.charts_frame.winfo_children():
            child.destroy()
        self._figure_canvases.clear()
        self._update_scrollregion()

    def refresh(self):
        """Reconstruye las gráficas según los parámetros seleccionados."""
        if self.db is None or not getattr(self.db, "is_open", False):
            self.clear()
            return

        selected_params = [name for name, var in self.param_vars.items() if var.get()]
        if not selected_params:
            self.clear()
            return

        # Limpiar gráficos anteriores
        self.clear()

        cols = 2
        row = 0
        col = 0

        for param_name in selected_params:
            fechas, valores = self._get_series_for_param(param_name)
            series = [(f, v) for f, v in zip(fechas, valores) if f is not None and v is not None]

            if not series:
                continue

            series.sort(key=lambda p: p[0])  # ordenar por fecha
            fechas_clean, valores_clean = zip(*series)

            fig = Figure(figsize=(4.5, 2.7), dpi=100)
            ax = fig.add_subplot(111)

            # Usamos fechas reales en el eje X
            ax.plot_date(list(fechas_clean), list(valores_clean), marker="o", linestyle="-")

            # Formato de fechas
            ax.xaxis.set_major_formatter(DateFormatter("%Y-%m-%d"))
            for label in ax.get_xticklabels():
                label.set_rotation(45)
                label.set_ha("right")
                label.set_fontsize(8)

            # Título
            info = self.PARAM_DEFS.get(param_name, {})
            label = info.get("label", param_name)
            ax.set_title(label, fontsize=10)
            ax.set_ylabel("Valor")

            # Rango normal, si existe en RangesManager (hematología)
            param_range: Optional[ParamRange] = None
            if self.ranges_manager is not None:
                param_range = self.ranges_manager.get_all().get(param_name)

            if param_range and (
                param_range.min_value is not None or param_range.max_value is not None
            ):
                ymin_plot = min(valores_clean)
                ymax_plot = max(valores_clean)

                ymin = param_range.min_value if param_range.min_value is not None else ymin_plot
                ymax = param_range.max_value if param_range.max_value is not None else ymax_plot

                ax.axhspan(ymin, ymax, alpha=0.15)

            ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.6)

            # Embebemos figura en Tk
            chart_container = ttk.Frame(self.charts_frame)
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
            self.charts_frame.grid_columnconfigure(c, weight=1)

        self._update_scrollregion()

    # ==========================================================
    #   Construcción de controles (checkboxes)
    # ==========================================================
    def _build_controls(self):
        ttk.Label(
            self.controls_frame,
            text="Parámetros a graficar:",
            font=("Segoe UI", 9, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=(0, 10), pady=(0, 5))

        current_row = 1

        for grupo, campos in self.PARAM_GROUPS:
            lbl = ttk.Label(
                self.controls_frame,
                text=grupo + ":",
                font=("Segoe UI", 9, "bold"),
            )
            lbl.grid(row=current_row, column=0, sticky="w", padx=(0, 5), pady=2)

            col = 1
            for name in campos:
                if name not in self.PARAM_DEFS:
                    continue

                info = self.PARAM_DEFS[name]
                text = info.get("label", name)

                var = tk.BooleanVar(value=False)
                chk = ttk.Checkbutton(
                    self.controls_frame,
                    text=text,
                    variable=var,
                    command=self._on_param_toggled,
                )
                chk.grid(row=current_row, column=col, sticky="w", padx=5, pady=2)

                self.param_vars[name] = var
                col += 1

            current_row += 1

        # Ensanchar columnas
        max_cols = max(
            (len(campos) for _grupo, campos in self.PARAM_GROUPS),
            default=1,
        ) + 1
        for c in range(max_cols):
            self.controls_frame.grid_columnconfigure(c, weight=1)

    def _on_param_toggled(self):
        self.refresh()

    # ==========================================================
    #   Datos y utilidades
    # ==========================================================
    def _get_series_for_param(self, param_name: str):
        """
        Devuelve (fechas, valores) para un parámetro dado.
        - fechas: lista de datetime
        - valores: lista de float o None
        """
        info = self.PARAM_DEFS.get(param_name)
        if not info or self.db is None or not getattr(self.db, "is_open", False):
            return [], []

        table = info["table"]

        # Seleccionamos el método list_* adecuado
        if table == "hematologia":
            rows = self.db.list_hematologia(limit=1000)
        elif table == "bioquimica":
            rows = self.db.list_bioquimica(limit=1000)
        elif table == "gasometria":
            rows = self.db.list_gasometria(limit=1000)
        elif table == "orina":
            rows = self.db.list_orina(limit=1000)
        else:
            return [], []

        fechas: List[Optional[datetime]] = []
        valores: List[Optional[float]] = []

        for r in rows:
            fecha_txt = str(r.get("fecha_analisis") or "").strip()
            try:
                dt = datetime.strptime(fecha_txt, "%Y-%m-%d")
            except ValueError:
                dt = None

            raw_val = r.get(param_name)
            if raw_val is None:
                val = None
            else:
                try:
                    # Permite float y strings tipo "123,4"
                    if isinstance(raw_val, str):
                        val = float(raw_val.replace(",", "."))
                    else:
                        val = float(raw_val)
                except (TypeError, ValueError):
                    val = None

            fechas.append(dt)
            valores.append(val)

        return fechas, valores

    # ==========================================================
    #   Scroll / geometry helpers
    # ==========================================================
    def _on_canvas_configure(self, event):
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)

    def _on_charts_configure(self, _event):
        self._update_scrollregion()

    def _update_scrollregion(self):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))