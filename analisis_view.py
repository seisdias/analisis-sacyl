# -*- coding: utf-8 -*-
"""
Vista de análisis de laboratorio usando tksheet.Sheet

Incluye:
- Hematología
- Bioquímica
- Orina (cuantitativa y cualitativa)

Funciones:
- Muestra todos los análisis fusionados por fecha de extracción.
- Permite activar/desactivar grupos de parámetros por categoría.
- Pinta en rojo las celdas fuera de rango según RangesManager
  (solo para parámetros numéricos con rango definido).
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

import ttkbootstrap as tb
from tksheet import Sheet

from ranges_config import RangesManager
from db_manager import HematologyDB  # solo para tipado y orden de campos

logger = logging.getLogger(__name__)


class AnalisisView(tb.Frame):
    """
    Frame que contiene:
      - Controles de filtrado por categorías en la parte superior.
      - Tabla central con los análisis (tksheet.Sheet).
    """

    DATE_FIELD_DB = "fecha_extraccion"

    # Orden de campos según las funciones de db_manager
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

    # Definición de categorías y campos (nombre interno, cabecera)
    # OJO: algunos campos de orina cualitativa se renombran como orina_* para no
    # pisar nombres de bioquímica (por ejemplo glucosa).
    CATEGORIES = {
        "Metadatos": [
            ("numero_peticion", "Nº petición"),
            ("origen", "Origen"),
        ],

        # --- Hematología ---
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
        "Fórmula leucocitaria (%)": [
            ("neutrofilos_pct", "Neutrófilos (%)"),
            ("linfocitos_pct", "Linfocitos (%)"),
            ("monocitos_pct", "Monocitos (%)"),
            ("eosinofilos_pct", "Eosinófilos (%)"),
            ("basofilos_pct", "Basófilos (%)"),
        ],
        "Fórmula leucocitaria (abs)": [
            ("neutrofilos_abs", "Neutrófilos (abs)"),
            ("linfocitos_abs", "Linfocitos (abs)"),
            ("monocitos_abs", "Monocitos (abs)"),
            ("eosinofilos_abs", "Eosinófilos (abs)"),
            ("basofilos_abs", "Basófilos (abs)"),
        ],
        "Serie plaquetar": [
            ("vpm", "VPM"),
        ],

        # --- Bioquímica ---
        "Bioquímica básica": [
            ("glucosa", "Glucosa"),
            ("urea", "Urea"),
            ("creatinina", "Creatinina"),
        ],
        "Electrolitos": [
            ("sodio", "Sodio"),
            ("potasio", "Potasio"),
            ("cloro", "Cloro"),
            ("calcio", "Calcio"),
            ("fosforo", "Fósforo"),
        ],
        "Perfil lipídico": [
            ("colesterol_total", "Colesterol total"),
            ("colesterol_hdl", "Colesterol HDL"),
            ("colesterol_ldl", "Colesterol LDL"),
            ("colesterol_no_hdl", "Colesterol no HDL"),
            ("trigliceridos", "Triglicéridos"),
            ("indice_riesgo", "Índice riesgo"),
        ],
        "Hierro y vitaminas": [
            ("hierro", "Hierro"),
            ("ferritina", "Ferritina"),
            ("vitamina_b12", "Vitamina B12"),
        ],

        # --- Orina cuantitativa ---
        "Orina cuantitativa": [
            ("ph", "pH orina"),
            ("densidad", "Densidad"),
            ("sodio_ur", "Sodio orina"),
            ("creatinina_ur", "Creatinina orina"),
            ("indice_albumina_creatinina", "Índice Alb/Cre"),
            ("albumina_ur", "Albúmina orina"),
        ],

        # --- Orina cualitativa (texto) ---
        "Orina cualitativa": [
            ("orina_color", "Color"),
            ("orina_aspecto", "Aspecto"),
            ("orina_glucosa", "Glucosa (tira)"),
            ("orina_proteinas", "Proteínas (tira)"),
            ("orina_cuerpos_cetonicos", "Cuerpos cetónicos"),
            ("orina_sangre", "Sangre"),
            ("orina_nitritos", "Nitritos"),
            ("orina_leucocitos_ests", "Leucocitos est."),
            ("orina_bilirrubina", "Bilirrubina"),
            ("orina_urobilinogeno", "Urobilinógeno"),
            ("orina_categoria_albuminuria", "Categoría albuminuria"),
        ],
    }

    def __init__(
        self,
        master,
        db: HematologyDB = None,
        ranges_manager: Optional[RangesManager] = None,
        **kwargs,
    ):
        super().__init__(master, **kwargs)

        self.db: HematologyDB = db
        self.ranges_manager: Optional[RangesManager] = ranges_manager
        self._rows_cache: List[Dict[str, Any]] = []

        # ====== FRAME SUPERIOR: CONTROLES DE CATEGORÍAS ======
        self.filters_frame = ttk.Frame(self)
        self.filters_frame.pack(side="top", fill="x", padx=5, pady=5)

        ttk.Label(
            self.filters_frame,
            text="Categorías a mostrar:",
            font=("Segoe UI", 9, "bold"),
        ).pack(side="left", padx=(0, 10))

        self.category_vars: Dict[str, tk.BooleanVar] = {}
        for cat_name in self.CATEGORIES.keys():
            var = tk.BooleanVar(value=True)  # por defecto todas activas
            chk = ttk.Checkbutton(
                self.filters_frame,
                text=cat_name,
                variable=var,
                command=self.refresh,
            )
            chk.pack(side="left", padx=5)
            self.category_vars[cat_name] = var

        ttk.Button(
            self.filters_frame,
            text="Marcar todo",
            command=self._select_all_categories,
        ).pack(side="left", padx=(15, 5))

        ttk.Button(
            self.filters_frame,
            text="Desmarcar todo",
            command=self._unselect_all_categories,
        ).pack(side="left", padx=5)

        # ====== FRAME CENTRAL: TABLA (tksheet.Sheet) ======
        table_container = ttk.Frame(self)
        table_container.pack(fill="both", expand=True, padx=5, pady=(0, 5))

        self.sheet = Sheet(
            table_container,
            data=[],
            headers=[],
            show_row_index=False,
            show_x_scrollbar=True,
            show_y_scrollbar=True,
        )
        self.sheet.enable_bindings(
            (
                "single_select",
                "row_select",
                "column_width_resize",
                "double_click_column_resize",
                "arrowkeys",
                "right_click_popup_menu",
                "select_all",
                "copy",
            )
        )
        self.sheet.pack(fill="both", expand=True)

    # ======================
    #   API PÚBLICA
    # ======================
    def set_db(self, db: HematologyDB):
        self.db = db

    def set_ranges_manager(self, ranges_manager: RangesManager):
        self.ranges_manager = ranges_manager
        self.refresh()

    def clear(self):
        self._rows_cache = []
        self.sheet.set_sheet_data(data=[])
        self.sheet.headers([])

    def refresh(self):
        """
        Recarga los datos desde la BD, fusiona hematología, bioquímica y orina
        por fecha, y reconstruye la tabla según las categorías activas.
        """
        logger.debug("AnalisisView.refresh() llamado")

        self._rows_cache = self._fetch_rows_from_db()
        logger.debug("Filas fusionadas obtenidas: %d", len(self._rows_cache))

        if not self._rows_cache:
            self.clear()
            return

        columns_spec = self._build_columns_spec()
        headers = [header for _field, header in columns_spec]

        data: List[List[Any]] = []
        for row in self._rows_cache:
            values = []
            for field_name, _header in columns_spec:
                values.append(row.get(field_name, ""))
            data.append(values)

        # Cargar en la hoja
        self.sheet.set_sheet_data(
            data=data,
            reset_col_positions=True,
            reset_row_positions=True,
            redraw=True,
        )
        self.sheet.headers(headers)

        # Ancho columnas
        for col_index in range(len(headers)):
            if col_index in (0, 1, 2):
                self.sheet.column_width(column=col_index, width=120)
            else:
                self.sheet.column_width(column=col_index, width=90)

        # Eliminar resaltados previos
        try:
            self.sheet.highlight_cells(cells="all", bg=None, fg=None, redraw=False)
        except Exception:
            pass

        # Resaltar fuera de rango (solo numéricos con rango definido)
        for r_idx, row_values in enumerate(data):
            for c_idx, cell_value in enumerate(row_values):
                field_name, _ = columns_spec[c_idx]
                if self._is_out_of_range(field_name, cell_value):
                    self.sheet.highlight_cells(
                        row=r_idx,
                        column=c_idx,
                        bg="#ffdddd",
                        fg="red",
                        redraw=False,
                    )

        self.sheet.redraw()

    # ======================
    #   MÉTODOS INTERNOS
    # ======================
    def _select_all_categories(self):
        for var in self.category_vars.values():
            var.set(True)
        self.refresh()

    def _unselect_all_categories(self):
        for var in self.category_vars.values():
            var.set(False)
        self.refresh()

    def _fetch_rows_from_db(self) -> List[Dict[str, Any]]:
        """
        Obtiene las filas de análisis desde la BD.

        Si HematologyDB ofrece list_combined_analyses(), usamos esa vista
        combinada (hematología + bioquímica + orina). En caso contrario,
        se hace un fallback al comportamiento antiguo (solo hematología).
        """
        if self.db is None or not getattr(self.db, "is_open", False):
            return []

        # Nueva ruta: vista combinada
        if hasattr(self.db, "list_combined_analyses"):
            rows = self.db.list_combined_analyses(limit=1000)
        else:
            # Compatibilidad antigua: solo tabla hematologia
            if not hasattr(self.db, "list_analyses"):
                return []
            tuples = self.db.list_analyses(limit=1000)
            rows = []
            for t in tuples:
                if len(t) != len(self.DB_FIELDS_ORDER):
                    continue
                row = {
                    field: value
                    for field, value in zip(self.DB_FIELDS_ORDER, t)
                }
                rows.append(row)

        # Ordenar por fecha_extraccion (texto ISO "YYYY-MM-DD")
        def parse_fecha(r: Dict[str, Any]):
            value = r.get(self.DATE_FIELD_DB, "")
            if not value:
                return datetime.min
            try:
                return datetime.strptime(str(value), "%Y-%m-%d")
            except ValueError:
                return datetime.min

        rows.sort(key=parse_fecha)
        return rows

    def _build_columns_spec(self) -> List[tuple]:
        """
        Construye la lista de columnas (field_name, header_text) a mostrar,
        según las categorías activas y los campos realmente disponibles.
        """
        if not self._rows_cache:
            return [(self.DATE_FIELD_DB, "Fecha")]

        available_fields = set()
        for row in self._rows_cache:
            available_fields.update(row.keys())

        columns = []

        # Fecha siempre al principio
        if self.DATE_FIELD_DB in available_fields:
            columns.append((self.DATE_FIELD_DB, "Fecha"))
        seen_fields = {f for f, _ in columns}

        # Categorías activas
        active_cats = [
            cat_name for cat_name, var in self.category_vars.items() if var.get()
        ]

        for cat_name in active_cats:
            for field_name, header_text in self.CATEGORIES.get(cat_name, []):
                if field_name in available_fields and field_name not in seen_fields:
                    columns.append((field_name, header_text))
                    seen_fields.add(field_name)

        # Si no hay nada salvo la fecha, añadimos algunos básicos
        if len(columns) <= 1:
            for fallback in [
                ("leucocitos", "Leucocitos"),
                ("hemoglobina", "Hemoglobina"),
                ("plaquetas", "Plaquetas"),
                ("glucosa", "Glucosa"),
            ]:
                field_name, header_text = fallback
                if field_name in available_fields and field_name not in seen_fields:
                    columns.append((field_name, header_text))
                    seen_fields.add(field_name)

        return columns

    def _is_out_of_range(self, field: str, value) -> bool:
        """
        Devuelve True si el valor está fuera de rango según ranges_manager.
        Solo aplica a campos numéricos con rango definido.
        """
        if self.ranges_manager is None:
            return False

        # Intentar convertir a float
        try:
            text = str(value).strip()
            if text == "":
                return False
            val = float(text.replace(",", "."))
        except (TypeError, ValueError):
            # Campos cualitativos, texto, etc.
            return False

        param = self.ranges_manager.get_all().get(field)
        if not param:
            return False

        min_v = param.min_value
        max_v = param.max_value

        if min_v is not None and val < min_v:
            return True
        if max_v is not None and val > max_v:
            return True
        return False