# -*- coding: utf-8 -*-
"""
Vista de análisis de hematología usando tksheet.Sheet

Requisitos:
    pip install tksheet

Esta vista:
- Muestra los análisis en una tabla tipo hoja de cálculo (Sheet).
- Ordena los análisis por fecha_extraccion (de la más antigua a la más nueva).
- Permite activar/desactivar grupos de parámetros por categoría.
- Pinta en rojo las celdas cuyos valores están fuera de rango
  según ranges_config.RangesManager.
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

import ttkbootstrap as tb
from tksheet import Sheet

from ranges_config import RangesManager
from db_manager import HematologyDB  # solo para tipado

logger = logging.getLogger(__name__)


class AnalisisView(tb.Frame):
    """
    Frame que contiene:
      - Controles de filtrado por categorías en la parte superior.
      - Tabla central con los análisis (tksheet.Sheet).
    """

    # Nombre del campo de fecha tal como viene de la BD
    DATE_FIELD_DB = "fecha_extraccion"

    # Definición de categorías y campos asociados (CAMPO_BD, CABECERA)
    CATEGORIES = {
        "Metadatos": [
            ("numero_peticion", "Nº petición"),
            ("origen", "Origen"),
        ],
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

    # Orden y nombres de columnas tal y como los devuelve HematologyDB.list_analyses()
    DB_FIELDS_ORDER = [
        "id",
        "fecha_extraccion",
        "numero_peticion",
        "origen",
        "leucocitos",
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
        "hematies",
        "hemoglobina",
        "hematocrito",
        "vcm",
        "hcm",
        "chcm",
        "rdw",
        "plaquetas",
        "vpm",
    ]

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

        # Botones rápidos
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
        """Asignar/actualizar objeto de base de datos."""
        self.db = db

    def set_ranges_manager(self, ranges_manager: RangesManager):
        """Actualizar el gestor de rangos (se usa tras cambiar configuración)."""
        self.ranges_manager = ranges_manager
        self.refresh()

    def clear(self):
        """Limpia la tabla por completo."""
        self._rows_cache = []
        self.sheet.set_sheet_data(data=[])
        self.sheet.headers([])

    def refresh(self):
        """
        Recarga los datos desde la BD y reconstruye la tabla,
        aplicando los filtros de categorías y coloreando celdas fuera de rango.
        """
        logger.debug("AnalisisView.refresh() llamado")

        # 1) Recuperar filas de la BD
        self._rows_cache = self._fetch_rows_from_db()
        logger.debug("Se han recuperado %d filas de la BD", len(self._rows_cache))

        if not self._rows_cache:
            logger.debug("No hay filas, se limpia la tabla")
            self.clear()
            return

        # 2) Determinar columnas a mostrar
        columns_spec = self._build_columns_spec()
        logger.debug("Columnas seleccionadas: %s", [c[0] for c in columns_spec])

        # 3) Preparar headers y datos para Sheet
        headers = [header for _field, header in columns_spec]

        data: List[List[Any]] = []
        for row in self._rows_cache:
            values = []
            for field_name, _header_text in columns_spec:
                values.append(row.get(field_name, ""))
            data.append(values)

        logger.debug("Se van a pintar %d filas en la hoja", len(data))

        # 4) Cargar datos en la hoja
        self.sheet.set_sheet_data(data=data, reset_col_positions=True,
                                  reset_row_positions=True, redraw=True)
        self.sheet.headers(headers)

        # Opcional: tamaños de columnas (las 3 primeras algo más anchas)
        for col_index in range(len(headers)):
            if col_index in (0, 1, 2):
                self.sheet.column_width(column=col_index, width=120)
            else:
                self.sheet.column_width(column=col_index, width=80)

        # 5) Quitar resaltados previos
        # tksheet permite "desresaltar" todo pasando None
        try:
            self.sheet.highlight_cells(
                cells="all", bg=None, fg=None, redraw=False
            )
        except Exception:
            # Algunas versiones pueden no necesitar este paso, lo ignoramos si falla
            pass

        # 6) Pintar celdas fuera de rango
        for r_idx, row_values in enumerate(data):
            for c_idx, cell_value in enumerate(row_values):
                field_name, _ = columns_spec[c_idx]
                if self._is_out_of_range(field_name, cell_value):
                    self.sheet.highlight_cells(
                        row=r_idx,
                        column=c_idx,
                        bg="#ffdddd",   # fondo suave
                        fg="red",
                        redraw=False,
                    )

        # Redibujar una sola vez después de todos los cambios
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
        Obtiene las filas de análisis desde la BD usando HematologyDB.list_analyses()
        y las ordena por fecha_extraccion (más antigua primero).

        Devuelve una lista de dicts con claves según DB_FIELDS_ORDER.
        """
        if self.db is None or not getattr(self.db, "is_open", False):
            return []

        if not hasattr(self.db, "list_analyses"):
            return []

        tuples = self.db.list_analyses(limit=1000)
        rows: List[Dict[str, Any]] = []

        for t in tuples:
            if len(t) != len(self.DB_FIELDS_ORDER):
                # Si cambia el esquema, la fila no se mapea bien
                continue
            row = {field: value for field, value in zip(self.DB_FIELDS_ORDER, t)}
            rows.append(row)

        # Ordenar por fecha_extraccion (texto en formato ISO "YYYY-MM-DD")
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

    def _build_columns_spec(self):
        """
        Construye la lista de columnas (field_name, header_text) a mostrar,
        en función de las categorías activas.

        Siempre incluirá la columna de fecha_extraccion al principio.
        Solo se incluirán columnas que existan en los datos.
        """
        if not self._rows_cache:
            return [(self.DATE_FIELD_DB, "Fecha")]

        available_fields = set()
        for row in self._rows_cache:
            available_fields.update(row.keys())

        columns = []

        # 1) Fecha siempre al principio
        if self.DATE_FIELD_DB in available_fields:
            columns.append((self.DATE_FIELD_DB, "Fecha"))

        seen_fields = {field for field, _ in columns}

        # 2) Añadir campos por categorías activas
        active_cats = [
            cat_name for cat_name, var in self.category_vars.items() if var.get()
        ]

        for cat_name in active_cats:
            for field_name, header_text in self.CATEGORIES.get(cat_name, []):
                if field_name in available_fields and field_name not in seen_fields:
                    columns.append((field_name, header_text))
                    seen_fields.add(field_name)

        # 3) Si no hay categorías activas o no se ha añadido nada, añadir básicos
        if len(columns) <= 1:
            for fallback in [
                ("leucocitos", "Leucocitos"),
                ("hemoglobina", "Hemoglobina"),
                ("plaquetas", "Plaquetas"),
            ]:
                field_name, header_text = fallback
                if field_name in available_fields and field_name not in seen_fields:
                    columns.append((field_name, header_text))
                    seen_fields.add(field_name)

        return columns

    def _is_out_of_range(self, field: str, value) -> bool:
        """
        Devuelve True si el valor está fuera de rango según ranges_manager.
        """
        if self.ranges_manager is None:
            return False

        # Intentar convertir a float (admitiendo coma decimal)
        try:
            text = str(value).strip()
            if text == "":
                return False
            val = float(text.replace(",", "."))
        except (TypeError, ValueError):
            return False

        param = self.ranges_manager.get_all().get(field)
        if not param:
            # No hay rango definido para este campo
            return False

        min_v = param.min_value
        max_v = param.max_value

        if min_v is not None and val < min_v:
            fuera = True
        elif max_v is not None and val > max_v:
            fuera = True
        else:
            fuera = False

        return fuera
