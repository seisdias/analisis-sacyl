# -*- coding: utf-8 -*-
"""
Panel de gráficas de evolución de parámetros de laboratorio.

Incluye:
- Hematología
- Bioquímica
- Orina cuantitativa

Cada parámetro:
- Tiene un checkbox para mostrar/ocultar la gráfica.
- Se dibuja valor vs fecha (eje X = tiempo real).
- Sombrea el rango normal usando RangesManager, si está definido.

Requisitos:
    pip install matplotlib
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime
from typing import Dict, Any, List, Optional

import matplotlib
matplotlib.use("TkAgg")   # Backend Tkinter
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates

from db_manager import HematologyDB
from ranges_config import RangesManager, ParamRange


class ChartsView(ttk.Frame):
    """
    Panel que contiene:
      - Una zona de checkboxes para elegir qué parámetros graficar.
      - Un área scrollable donde se colocan las gráficas en rejilla.
    """

    # Parámetros graficables (solo NUMÉRICOS)
    PARAMS = [
        # Hematología
        ("leucocitos",        "Leucocitos"),
        ("neutrofilos_pct",   "Neutrófilos (%)"),
        ("linfocitos_pct",    "Linfocitos (%)"),
        ("monocitos_pct",     "Monocitos (%)"),
        ("eosinofilos_pct",   "Eosinófilos (%)"),
        ("basofilos_pct",     "Basófilos (%)"),
        ("neutrofilos_abs",   "Neutrófilos (abs)"),
        ("linfocitos_abs",    "Linfocitos (abs)"),
        ("monocitos_abs",     "Monocitos (abs)"),
        ("eosinofilos_abs",   "Eosinófilos (abs)"),
        ("basofilos_abs",     "Basófilos (abs)"),
        ("hematies",          "Hematíes"),
        ("hemoglobina",       "Hemoglobina"),
        ("hematocrito",       "Hematocrito"),
        ("vcm",               "VCM"),
        ("hcm",               "HCM"),
        ("chcm",              "CHCM"),
        ("rdw",               "RDW"),
        ("plaquetas",         "Plaquetas"),
        ("vpm",               "VPM"),

        # Bioquímica básica
        ("glucosa",           "Glucosa"),
        ("urea",              "Urea"),
        ("creatinina",        "Creatinina"),

        # Electrolitos / iones
        ("sodio",             "Sodio"),
        ("potasio",           "Potasio"),
        ("cloro",             "Cloro"),
        ("calcio",            "Calcio"),
        ("fosforo",           "Fósforo"),

        # Perfil lipídico
        ("colesterol_total",  "Colesterol total"),
        ("colesterol_hdl",    "Colesterol HDL"),
        ("colesterol_ldl",    "Colesterol LDL"),
        ("colesterol_no_hdl", "Colesterol no HDL"),
        ("trigliceridos",     "Triglicéridos"),
        ("indice_riesgo",     "Índice riesgo"),

        # Hierro y vitaminas
        ("hierro",            "Hierro"),
        ("ferritina",         "Ferritina"),
        ("vitamina_b12",      "Vitamina B12"),

        # Orina cuantitativa
        ("ph",                        "pH orina"),
        ("densidad",                  "Densidad"),
        ("sodio_ur",                  "Sodio orina"),
        ("creatinina_ur",             "Creatinina orina"),
        ("indice_albumina_creatinina","Índice Alb/Cre"),
        ("albumina_ur",               "Albúmina orina"),
    ]

    PARAM_LABELS = {name: label for name, label in PARAMS}

    # Grupos para organizar los checkboxes
    PARAM_GROUPS = [
        ("Hemograma básico",
         ["leucocitos", "hematies", "hemoglobina", "hematocrito", "vcm", "hcm", "chcm", "rdw", "plaquetas", "vpm"]),
        ("Fórmula leucocitaria (%)",
         ["neutrofilos_pct", "linfocitos_pct", "monocitos_pct", "eosinofilos_pct", "basofilos_pct"]),
        ("Fórmula leucocitaria (abs)",
         ["neutrofilos_abs", "linfocitos_abs", "monocitos_abs", "eosinofilos_abs", "basofilos_abs"]),
        ("Bioquímica básica",
         ["glucosa", "urea", "creatinina"]),
        ("Electrolitos / iones",
         ["sodio", "potasio", "cloro", "calcio", "fosforo"]),
        ("Perfil lipídico",
         ["colesterol_total", "colesterol_hdl", "colesterol_ldl", "colesterol_no_hdl", "trigliceridos", "indice_riesgo"]),
        ("Hierro y vitaminas",
         ["hierro", "ferritina", "vitamina_b12"]),
        ("Orina cuantitativa",
         ["ph", "densidad", "sodio_ur", "creatinina_ur",
          "indice_albumina_creatinina", "albumina_ur"]),
    ]

    # Orden de campos de las consultas a la BD
    HEMATO_FIELDS = HematologyDB.DB_FIELDS_ORDER

    BIO_FIELDS = [
        "id",
        "fecha_extraccion",
        "numero_peticion",
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
    ]

    ORINA_FIELDS = [
        "id",
        "fecha_extraccion",
        "numero_peticion",
        "color",
        "aspecto",
        "ph",
        "densidad",
        "glucosa",
        "proteinas",
        "cuerpos_cetonicos",
        "sangre",
        "nitritos",
        "leucocitos_ests",
        "bilirrubina",
        "urobilinogeno",
        "sodio_ur",
        "creatinina_ur",
        "indice_albumina_creatinina",
        "categoria_albuminuria",
        "albumina_ur",
    ]

    def __init__(
        self,
        master,
        db: Optional[HematologyDB] = None,
        ranges_manager: Optional[RangesManager] = None,
        **kwargs
    ):
        super().__init__(master, **kwargs)

        self.db: Optional[HematologyDB] = db
        self.ranges_manager: Optional[RangesManager] = ranges_manager

        # checkboxes
        self.param_vars: Dict[str, tk.BooleanVar] = {}

        # referencias a canvases de matplotlib
        self._figure_canvases: List[FigureCanvasTkAgg] = []

        # ----- Zona superior: controles -----
        self.controls_frame = ttk.Frame(self)
        self.controls_frame.pack(side="top", fill="x", padx=5, pady=5)
        self._build_controls()

        # ----- Zona inferior: canvas scrollable con gráficas -----
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(
            self, orient="vertical", command=self.canvas.yview
        )
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.charts_frame = ttk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.charts_frame,
            anchor="nw"
        )

        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.charts_frame.bind("<Configure>", self._on_charts_configure)

    # ==========================
    #   API pública
    # ==========================
    def set_db(self, db: HematologyDB):
        self.db = db

    def set_ranges_manager(self, ranges_manager: RangesManager):
        self.ranges_manager = ranges_manager

    def clear(self):
        for child in self.charts_frame.winfo_children():
            child.destroy()
        self._figure_canvases.clear()
        self._update_scrollregion()

    def refresh(self):
        """
        Reconstruye las gráficas según:
          - Parámetros seleccionados.
          - Datos fusionados de hematología, bioquímica y orina cuantitativa.
        """
        if self.db is None or not getattr(self.db, "is_open", False):
            self.clear()
            return

        analyses = self._fetch_analyses()
        if not analyses:
            self.clear()
            return

        self.clear()

        selected_params = [
            name for name, var in self.param_vars.items() if var.get()
        ]

        if not selected_params:
            self._update_scrollregion()
            return

        cols = 2
        row = 0
        col = 0

        for param_name in selected_params:
            fig = Figure(figsize=(4, 2.5), dpi=100)
            ax = fig.add_subplot(111)

            fechas, valores = self._extract_series(analyses, param_name)

            series = [(f, v) for f, v in zip(fechas, valores) if v is not None]
            if not series:
                continue

            fechas_clean, valores_clean = zip(*series)

            # Eje X = fechas reales
            ax.plot_date(
                fechas_clean,
                valores_clean,
                marker="o",
                linestyle="-",
            )

            # Formato de fechas en eje X
            ax.xaxis.set_major_locator(mdates.AutoDateLocator())
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
            fig.autofmt_xdate(rotation=45)

            label = self.PARAM_LABELS.get(param_name, param_name)
            ax.set_title(label, fontsize=10)
            ax.set_ylabel("Valor")

            # Rango normal (sombreado)
            param_range: Optional[ParamRange] = None
            if self.ranges_manager is not None:
                param_range = self.ranges_manager.get_all().get(param_name)

            if param_range and (
                param_range.min_value is not None or param_range.max_value is not None
            ):
                ymin = (
                    param_range.min_value
                    if param_range.min_value is not None
                    else min(valores_clean)
                )
                ymax = (
                    param_range.max_value
                    if param_range.max_value is not None
                    else max(valores_clean)
                )
                if ymin > ymax:  # por si acaso
                    ymin, ymax = ymax, ymin
                ax.axhspan(ymin, ymax, alpha=0.15)

            ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.6)

            # Embebemos en Tk
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

    # ==========================
    #   Controles (checkboxes)
    # ==========================
    def _build_controls(self):
        ttk.Label(
            self.controls_frame,
            text="Parámetros a graficar:",
            font=("Segoe UI", 9, "bold")
        ).grid(row=0, column=0, sticky="w", padx=(0, 10), pady=(0, 5))

        current_row = 1

        for grupo, campos in self.PARAM_GROUPS:
            lbl = ttk.Label(
                self.controls_frame,
                text=grupo + ":",
                font=("Segoe UI", 9, "bold")
            )
            lbl.grid(row=current_row, column=0, sticky="w", padx=(0, 5), pady=2)

            col = 1
            for name in campos:
                if name not in self.PARAM_LABELS:
                    continue

                label = self.PARAM_LABELS[name]
                var = tk.BooleanVar(value=False)

                chk = ttk.Checkbutton(
                    self.controls_frame,
                    text=label,
                    variable=var,
                    command=self._on_param_toggled
                )
                chk.grid(row=current_row, column=col, sticky="w", padx=5, pady=2)

                self.param_vars[name] = var
                col += 1

            current_row += 1

        max_cols = max(
            (len(campos) for _grupo, campos in self.PARAM_GROUPS),
            default=1
        ) + 1

        for c in range(max_cols):
            self.controls_frame.grid_columnconfigure(c, weight=1)

    def _on_param_toggled(self):
        self.refresh()

    # ==========================
    #   Datos y utilidades
    # ==========================
    def _fetch_analyses(self) -> List[Dict[str, Any]]:
        """
        Fusiona por fecha_extraccion:
          - hematología (hematologia)
          - bioquímica (bioquimica)
          - orina (solo cuantitativa)
        """
        if self.db is None or not getattr(self.db, "is_open", False):
            return []

        combined: Dict[str, Dict[str, Any]] = {}

        # --- Hematología ---
        try:
            tuples_hema = self.db.list_analyses(limit=1000)
        except Exception:
            tuples_hema = []

        for t in tuples_hema:
            if len(t) != len(self.HEMATO_FIELDS):
                continue
            row = {field: value for field, value in zip(self.HEMATO_FIELDS, t)}
            fecha = str(row.get("fecha_extraccion") or "")
            if not fecha:
                continue
            d = combined.setdefault(fecha, {"fecha_extraccion": fecha})
            row.pop("id", None)
            d.update(row)

        # --- Bioquímica ---
        if hasattr(self.db, "list_bioquimica"):
            try:
                tuples_bio = self.db.list_bioquimica(limit=1000)
            except Exception:
                tuples_bio = []
        else:
            tuples_bio = []

        for t in tuples_bio:
            if len(t) != len(self.BIO_FIELDS):
                continue
            row = {field: value for field, value in zip(self.BIO_FIELDS, t)}
            fecha = str(row.get("fecha_extraccion") or "")
            if not fecha:
                continue
            d = combined.setdefault(fecha, {"fecha_extraccion": fecha})
            row.pop("id", None)
            # nº petición solo si no existía ya
            num_pet = row.pop("numero_peticion", None)
            if "numero_peticion" not in d and num_pet:
                d["numero_peticion"] = num_pet
            d.update(row)

        # --- Orina (solo cuantitativos) ---
        if hasattr(self.db, "list_orina"):
            try:
                tuples_orina = self.db.list_orina(limit=1000)
            except Exception:
                tuples_orina = []
        else:
            tuples_orina = []

        for t in tuples_orina:
            if len(t) != len(self.ORINA_FIELDS):
                continue
            row = {field: value for field, value in zip(self.ORINA_FIELDS, t)}
            fecha = str(row.get("fecha_extraccion") or "")
            if not fecha:
                continue
            d = combined.setdefault(fecha, {"fecha_extraccion": fecha})
            row.pop("id", None)
            num_pet = row.pop("numero_peticion", None)
            if "numero_peticion" not in d and num_pet:
                d["numero_peticion"] = num_pet

            for key in [
                "ph",
                "densidad",
                "sodio_ur",
                "creatinina_ur",
                "indice_albumina_creatinina",
                "albumina_ur",
            ]:
                if key in row:
                    d[key] = row[key]

        # Pasamos a lista y ordenamos por fecha
        def parse_fecha(fecha_txt: str) -> datetime:
            if not fecha_txt:
                return datetime.min
            try:
                return datetime.strptime(fecha_txt, "%Y-%m-%d")
            except ValueError:
                return datetime.min

        rows: List[Dict[str, Any]] = []
        for fecha, d in combined.items():
            r = dict(d)
            r["_fecha_dt"] = parse_fecha(fecha)
            rows.append(r)

        rows.sort(key=lambda r: r["_fecha_dt"])
        for r in rows:
            r.pop("_fecha_dt", None)
        return rows

    def _extract_series(self, rows: List[Dict[str, Any]], field: str):
        fechas = []
        valores = []
        for r in rows:
            fecha_txt = str(r.get("fecha_extraccion") or "")
            try:
                fecha_dt = datetime.strptime(fecha_txt, "%Y-%m-%d")
            except ValueError:
                fecha_dt = datetime.min
            fechas.append(fecha_dt)
            valores.append(r.get(field))
        return fechas, valores

    def _on_canvas_configure(self, event):
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)

    def _on_charts_configure(self, _event):
        self._update_scrollregion()

    def _update_scrollregion(self):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))