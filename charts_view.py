# -*- coding: utf-8 -*-
"""
Panel de gráficas de evolución de parámetros de laboratorio.

- Muestra gráficas individuales por parámetro (valor vs fecha).
- Cada parámetro tiene un checkbox para mostrar/ocultar su gráfica.
- Integra:
    - HematologyDB (hematología, bioquímica, orina).
    - RangesManager (para sombrear el rango normal).

Requisitos:
    pip install matplotlib
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime
from typing import Dict, Any, List, Optional

import matplotlib
matplotlib.use("TkAgg")   # Backend para Tkinter

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

    # -----------------------------
    #  Definición de parámetros
    # -----------------------------
    # nombre_interno, etiqueta
    PARAMS = [
        # Hematología – hemograma básico
        ("leucocitos",        "Leucocitos"),
        ("hematies",          "Hematíes"),
        ("hemoglobina",       "Hemoglobina"),
        ("hematocrito",       "Hematocrito"),
        ("vcm",               "VCM"),
        ("hcm",               "HCM"),
        ("chcm",              "CHCM"),
        ("rdw",               "RDW"),
        ("plaquetas",         "Plaquetas"),
        ("vpm",               "VPM"),

        # Hematología – fórmula leucocitaria
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

    # Mapa rápido nombre -> etiqueta
    PARAM_LABELS = {name: label for name, label in PARAMS}

    # Alias de campos "amigables" -> nombres reales en la BD combinada
    FIELD_ALIASES = {
        "ph_orina": "ph_orina",                 # ya lo crea list_combined_analyses
        "sodio_orina": "sodio_orina",           # idem
        "creatinina_orina": "creatinina_orina",
        "albumina_orina": "albumina_orina",
    }

    # Indica de qué tabla viene cada parámetro
    # (por defecto hematología si no está en el diccionario)
    PARAM_SOURCE: Dict[str, str] = {
        # Bioquímica
        "glucosa": "bioquimica",
        "urea": "bioquimica",
        "creatinina": "bioquimica",
        "sodio": "bioquimica",
        "potasio": "bioquimica",
        "cloro": "bioquimica",
        "calcio": "bioquimica",
        "fosforo": "bioquimica",
        "colesterol_total": "bioquimica",
        "colesterol_hdl": "bioquimica",
        "colesterol_ldl": "bioquimica",
        "colesterol_no_hdl": "bioquimica",
        "trigliceridos": "bioquimica",
        "indice_riesgo": "bioquimica",
        "hierro": "bioquimica",
        "ferritina": "bioquimica",
        "vitamina_b12": "bioquimica",

        # Orina cuantitativa
        "ph": "orina",
        "densidad": "orina",
        "sodio_ur": "orina",
        "creatinina_ur": "orina",
        "indice_albumina_creatinina": "orina",
        "albumina_ur": "orina",
    }

    # Grupos de parámetros para los checkboxes
    PARAM_GROUPS = [
        (
            "Hemograma básico",
            ["leucocitos", "hematies", "hemoglobina", "hematocrito",
             "vcm", "hcm", "chcm", "rdw", "plaquetas", "vpm"],
        ),
        (
            "Fórmula leucocitaria (%)",
            ["neutrofilos_pct", "linfocitos_pct", "monocitos_pct",
             "eosinofilos_pct", "basofilos_pct"],
        ),
        (
            "Fórmula leucocitaria (abs)",
            ["neutrofilos_abs", "linfocitos_abs", "monocitos_abs",
             "eosinofilos_abs", "basofilos_abs"],
        ),
        (
            "Bioquímica básica",
            ["glucosa", "urea", "creatinina"],
        ),
        (
            "Electrolitos / iones",
            ["sodio", "potasio", "cloro", "calcio", "fosforo"],
        ),
        (
            "Perfil lipídico",
            ["colesterol_total", "colesterol_hdl", "colesterol_ldl",
             "colesterol_no_hdl", "trigliceridos", "indice_riesgo"],
        ),
        (
            "Hierro y vitaminas",
            ["hierro", "ferritina", "vitamina_b12"],
        ),
        (
            "Orina cuantitativa",
            ["ph", "densidad", "sodio_ur", "creatinina_ur",
             "indice_albumina_creatinina", "albumina_ur"],
        ),
    ]

    # Orden de campos devueltos por las consultas de db_manager
    HEMATO_FIELDS = [
        "id", "fecha_extraccion", "numero_peticion", "origen",
        "leucocitos",
        "neutrofilos_pct", "linfocitos_pct", "monocitos_pct",
        "eosinofilos_pct", "basofilos_pct",
        "neutrofilos_abs", "linfocitos_abs", "monocitos_abs",
        "eosinofilos_abs", "basofilos_abs",
        "hematies", "hemoglobina", "hematocrito", "vcm",
        "hcm", "chcm", "rdw",
        "plaquetas", "vpm",
    ]

    BIO_FIELDS = [
        "id", "fecha_extraccion", "numero_peticion",
        "glucosa", "urea", "creatinina",
        "sodio", "potasio", "cloro", "calcio", "fosforo",
        "colesterol_total", "colesterol_hdl", "colesterol_ldl",
        "colesterol_no_hdl", "trigliceridos", "indice_riesgo",
        "hierro", "ferritina", "vitamina_b12",
    ]

    ORINA_FIELDS = [
        "id", "fecha_extraccion", "numero_peticion",
        "color", "aspecto",
        "ph", "densidad",
        "glucosa", "proteinas", "cuerpos_cetonicos",
        "sangre", "nitritos", "leucocitos_ests",
        "bilirrubina", "urobilinogeno",
        "sodio_ur", "creatinina_ur",
        "indice_albumina_creatinina", "categoria_albuminuria",
        "albumina_ur",
    ]

    # -----------------------------
    #  Inicialización
    # -----------------------------
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

        # Parámetros seleccionados: { "leucocitos": BooleanVar, ... }
        self.param_vars: Dict[str, tk.BooleanVar] = {}

        # Referencias a los canvases de matplotlib para evitar GC
        self._figure_canvases: List[FigureCanvasTkAgg] = []

        # Cachés de datos
        self._hematology_rows: List[Dict[str, Any]] = []
        self._bio_rows: List[Dict[str, Any]] = []
        self._orina_rows: List[Dict[str, Any]] = []

        # ----- Zona superior: controles de selección -----
        self.controls_frame = ttk.Frame(self)
        self.controls_frame.pack(side="top", fill="x", padx=5, pady=5)

        self._build_controls()

        # ----- Zona inferior: canvas scrollable con las gráficas -----
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
            anchor="nw",
        )

        # Ajustes de scroll
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

        # --- Cargar datos de las tres tablas una sola vez ---
        self._hematology_rows = self._fetch_rows_from_table(
            self.db.list_analyses, self.HEMATO_FIELDS
        )
        self._bio_rows = self._fetch_rows_from_table(
            getattr(self.db, "list_bioquimica", None), self.BIO_FIELDS
        )
        self._orina_rows = self._fetch_rows_from_table(
            getattr(self.db, "list_orina", None), self.ORINA_FIELDS
        )

        if (
            not self._hematology_rows
            and not self._bio_rows
            and not self._orina_rows
        ):
            self.clear()
            return

        # Limpiamos gráficos anteriores
        self.clear()

        # Parámetros seleccionados
        selected_params = [
            name for name, var in self.param_vars.items() if var.get()
        ]

        if not selected_params:
            self._update_scrollregion()
            return

        # Distribuimos en rejilla (2 columnas)
        cols = 2
        row = 0
        col = 0

        for param_name in selected_params:
            source = self.PARAM_SOURCE.get(param_name, "hematologia")

            if source == "bioquimica":
                rows = self._bio_rows
            elif source == "orina":
                rows = self._orina_rows
            else:
                rows = self._hematology_rows

            fechas, valores = self._extract_series(rows, param_name)

            # Filtrar valores None
            series = [(f, v) for f, v in zip(fechas, valores) if v is not None]
            if not series:
                continue

            fechas_clean, valores_clean = zip(*series)

            # --- Construir figura ---
            fig = Figure(figsize=(4, 2.5), dpi=100)
            ax = fig.add_subplot(111)

            # Eje X temporal real
            x = mdates.date2num(list(fechas_clean))
            ax.plot_date(x, list(valores_clean), "-o")  # fmt "-o" -> sin warning

            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
            fig.autofmt_xdate(rotation=45)

            label = self.PARAM_LABELS.get(param_name, param_name)
            ax.set_title(label, fontsize=10)
            ax.set_ylabel("Valor")

            # Rango normal, si existe
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
                ax.axhspan(ymin, ymax, alpha=0.15)

            ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.6)

            # Embebemos la figura en Tk
            chart_container = ttk.Frame(self.charts_frame)
            chart_container.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

            canvas = FigureCanvasTkAgg(fig, master=chart_container)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)

            self._figure_canvases.append(canvas)

            # Avanzamos en la rejilla
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
        """
        Construye los checkboxes de selección de parámetros
        organizados por grupos en líneas horizontales.
        """
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
                if name not in self.PARAM_LABELS:
                    continue

                label = self.PARAM_LABELS[name]
                var = tk.BooleanVar(value=False)

                chk = ttk.Checkbutton(
                    self.controls_frame,
                    text=label,
                    variable=var,
                    command=self._on_param_toggled,
                )
                chk.grid(row=current_row, column=col, sticky="w", padx=5, pady=2)

                self.param_vars[name] = var
                col += 1

            current_row += 1

        # permitir ligera expansión horizontal
        max_cols = max(
            (len(campos) for _grupo, campos in self.PARAM_GROUPS),
            default=1,
        ) + 1

        for c in range(max_cols):
            self.controls_frame.grid_columnconfigure(c, weight=1)

    def _on_param_toggled(self):
        """Se llama cuando el usuario marca/desmarca cualquier checkbox."""
        self.refresh()

    # ==========================
    #   Datos y utilidades
    # ==========================
    def _fetch_rows_from_table(
        self,
        list_fn,
        fields_order: List[str],
    ) -> List[Dict[str, Any]]:
        """
        Recupera filas de una tabla (hematología/bioquímica/orina)
        usando la función de listado correspondiente del db_manager.
        """
        if list_fn is None or self.db is None:
            return []

        try:
            tuples = list_fn(limit=1000)
        except Exception:
            return []

        rows: List[Dict[str, Any]] = []

        for t in tuples:
            if len(t) != len(fields_order):
                continue
            row = {field: value for field, value in zip(fields_order, t)}

            fecha_txt = str(row.get("fecha_extraccion") or "")
            try:
                row["_fecha_dt"] = datetime.strptime(fecha_txt, "%Y-%m-%d")
            except ValueError:
                row["_fecha_dt"] = datetime.min

            rows.append(row)

        rows.sort(key=lambda r: r["_fecha_dt"])
        return rows

    def _extract_series(self, rows: List[Dict[str, Any]], field: str):
        """
        Devuelve una tupla (fechas, valores) para el campo indicado.
        """
        fechas = [r.get("_fecha_dt", datetime.min) for r in rows]
        valores = [r.get(field) for r in rows]
        return fechas, valores

    # ==========================
    #   Scroll / geometry
    # ==========================
    def _on_canvas_configure(self, event):
        """Ajusta el ancho del frame interior al ancho del canvas."""
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)

    def _on_charts_configure(self, _event):
        """Actualiza la región scrollable al cambiar el tamaño del frame."""
        self._update_scrollregion()

    def _update_scrollregion(self):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))