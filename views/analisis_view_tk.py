# -*- coding: utf-8 -*-
"""
Vista de análisis de laboratorio usando tksheet.Sheet

- Muestra los análisis en 4 pestañas:
    • Hematología
    • Bioquímica
    • Gasometría
    • Orina
- Cada pestaña es una tabla tipo hoja de cálculo (Sheet).
- La pestaña de Hematología pinta en rojo las celdas fuera de rango
  según ranges_config.RangesManager.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

from tksheet import Sheet

from ranges_config import RangesManager
from db_manager import HematologyDB  # solo para tipado

logger = logging.getLogger(__name__)


class AnalisisView(ttk.Frame):
    """
    Frame principal con un Notebook y 4 pestañas:
      - Hematología
      - Bioquímica
      - Gasometría
      - Orina
    """

    # Orden de campos esperados para cada tabla (según db_manager)
    HEMA_FIELDS = [
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

    BIOQ_FIELDS = [
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

    # Mapeo a cabeceras legibles
    HEMA_HEADERS = {
        "fecha_extraccion": "Fecha",
        "numero_peticion": "Nº petición",
        "origen": "Origen",
        "leucocitos": "Leucocitos (10³/µL)",
        "neutrofilos_pct": "Neutrófilos %",
        "linfocitos_pct": "Linfocitos %",
        "monocitos_pct": "Monocitos %",
        "eosinofilos_pct": "Eosinófilos %",
        "basofilos_pct": "Basófilos %",
        "neutrofilos_abs": "Neutrófilos abs (10³/µL)",
        "linfocitos_abs": "Linfocitos abs (10³/µL)",
        "monocitos_abs": "Monocitos abs (10³/µL)",
        "eosinofilos_abs": "Eosinófilos abs (10³/µL)",
        "basofilos_abs": "Basófilos abs (10³/µL)",
        "hematies": "Hematíes (10⁶/µL)",
        "hemoglobina": "Hemoglobina (g/dL)",
        "hematocrito": "Hematocrito (%)",
        "vcm": "VCM (fL)",
        "hcm": "HCM (pg)",
        "chcm": "CHCM (g/dL)",
        "rdw": "RDW (%)",
        "plaquetas": "Plaquetas (10³/µL)",
        "vpm": "VPM (fL)",
    }

    BIOQ_HEADERS = {
        "fecha_extraccion": "Fecha",
        "numero_peticion": "Nº petición",
        "glucosa": "Glucosa",
        "urea": "Urea",
        "creatinina": "Creatinina",
        "sodio": "Sodio",
        "potasio": "Potasio",
        "cloro": "Cloro",
        "calcio": "Calcio",
        "fosforo": "Fósforo",
        "colesterol_total": "Colesterol total",
        "colesterol_hdl": "Colesterol HDL",
        "colesterol_ldl": "Colesterol LDL",
        "colesterol_no_hdl": "Colesterol no HDL",
        "trigliceridos": "Triglicéridos",
        "indice_riesgo": "Índice riesgo",
        "hierro": "Hierro",
        "ferritina": "Ferritina",
        "vitamina_b12": "Vitamina B12",
    }

    ORINA_HEADERS = {
        "fecha_extraccion": "Fecha",
        "numero_peticion": "Nº petición",
        "color": "Color",
        "aspecto": "Aspecto",
        "ph": "pH",
        "densidad": "Densidad",
        "glucosa": "Glucosa (tira)",
        "proteinas": "Proteínas",
        "cuerpos_cetonicos": "Cuerpos cetónicos",
        "sangre": "Sangre",
        "nitritos": "Nitritos",
        "leucocitos_ests": "Leucocitos est.",
        "bilirrubina": "Bilirrubina",
        "urobilinogeno": "Urobilinógeno",
        "sodio_ur": "Sodio orina",
        "creatinina_ur": "Creatinina orina",
        "indice_albumina_creatinina": "Índice Alb/Cre",
        "categoria_albuminuria": "Cat. albuminuria",
        "albumina_ur": "Albúmina orina",
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

        # Notebook con pestañas
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        # ---- Pestaña Hematología ----
        self.tab_hema = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_hema, text="Hematología")

        self.sheet_hema = self._create_sheet(self.tab_hema)

        # ---- Pestaña Bioquímica ----
        self.tab_bioq = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_bioq, text="Bioquímica")

        self.sheet_bioq = self._create_sheet(self.tab_bioq)

        # ---- Pestaña Gasometría ----
        self.tab_gaso = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_gaso, text="Gasometría")

        self.sheet_gaso = self._create_sheet(self.tab_gaso)

        # ---- Pestaña Orina ----
        self.tab_orina = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_orina, text="Orina")

        self.sheet_orina = self._create_sheet(self.tab_orina)

    # ============================================================
    #   Fabricación de Sheet
    # ============================================================
    def _create_sheet(self, parent) -> Sheet:
        sheet = Sheet(
            parent,
            data=[],
            headers=[],
            show_row_index=False,
            show_x_scrollbar=True,
            show_y_scrollbar=True,
        )
        sheet.enable_bindings(
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
        sheet.pack(fill="both", expand=True)
        return sheet

    # ============================================================
    #   API pública
    # ============================================================
    def set_db(self, db: HematologyDB):
        self.db = db

    def set_ranges_manager(self, ranges_manager: RangesManager):
        self.ranges_manager = ranges_manager

    def clear(self):
        """Limpia todas las pestañas."""
        for sheet in (self.sheet_hema, self.sheet_bioq, self.sheet_gaso, self.sheet_orina):
            sheet.set_sheet_data([])
            sheet.headers([])

    def refresh(self):
        """
        Recarga los datos de la BD en todas las pestañas.
        """
        logger.debug("AnalisisView.refresh()")

        if self.db is None or not getattr(self.db, "is_open", False):
            self.clear()
            return

        self._refresh_hematologia()
        self._refresh_bioquimica()
        self._refresh_gasometria()
        self._refresh_orina()

    # ============================================================
    #   Hematología
    # ============================================================
    def _refresh_hematologia(self):
        rows = self._get_rows_generic(
            list_method_name="list_hematologia",
            fallback_name="list_analyses",  # compatibilidad con versiones antiguas
            fields_order=self.HEMA_FIELDS,
        )

        if not rows:
            self.sheet_hema.set_sheet_data([])
            self.sheet_hema.headers([])
            return

        # No mostramos el ID en la tabla
        fields = self.HEMA_FIELDS[1:]
        headers = [self.HEMA_HEADERS.get(f, f) for f in fields]

        data: List[List[Any]] = []
        for row in rows:
            data.append([row.get(f, "") for f in fields])

        self.sheet_hema.set_sheet_data(
            data=data,
            reset_col_positions=True,
            reset_row_positions=True,
            redraw=True,
        )
        self.sheet_hema.headers(headers)

        # Ajuste de anchura básica
        for i in range(len(headers)):
            if i == 0:
                self.sheet_hema.column_width(i, 110)  # fecha
            else:
                self.sheet_hema.column_width(i, 90)

        # Quitar resaltados previos
        try:
            self.sheet_hema.highlight_cells(cells="all", bg=None, fg=None, redraw=False)
        except Exception:
            pass

        # Pintar fuera de rango
        self._apply_out_of_range_highlight(self.sheet_hema, rows, fields)

        self.sheet_hema.redraw()

    # ============================================================
    #   Bioquímica
    # ============================================================
    def _refresh_bioquimica(self):
        if not hasattr(self.db, "list_bioquimica"):
            self.sheet_bioq.set_sheet_data([])
            self.sheet_bioq.headers([])
            return

        rows = self._get_rows_generic(
            list_method_name="list_bioquimica",
            fallback_name=None,
            fields_order=self.BIOQ_FIELDS,
        )

        if not rows:
            self.sheet_bioq.set_sheet_data([])
            self.sheet_bioq.headers([])
            return

        fields = self.BIOQ_FIELDS[1:]  # sin id
        headers = [self.BIOQ_HEADERS.get(f, f) for f in fields]

        data: List[List[Any]] = []
        for row in rows:
            data.append([row.get(f, "") for f in fields])

        self.sheet_bioq.set_sheet_data(
            data=data,
            reset_col_positions=True,
            reset_row_positions=True,
            redraw=True,
        )
        self.sheet_bioq.headers(headers)

        for i in range(len(headers)):
            if i == 0:
                self.sheet_bioq.column_width(i, 110)
            else:
                self.sheet_bioq.column_width(i, 90)

        self.sheet_bioq.redraw()

    # ============================================================
    #   Gasometría
    # ============================================================
    def _refresh_gasometria(self):
        """
        La implementación depende de si existe list_gasometria en la BD.
        Si aún no se ha creado la tabla de gasometría, se deja vacía.
        """
        if not hasattr(self.db, "list_gasometria"):
            self.sheet_gaso.set_sheet_data([])
            self.sheet_gaso.headers(["(No hay tabla de gasometría configurada)"])
            return

        rows = self.db.list_gasometria(limit=1000)

        if not rows:
            self.sheet_gaso.set_sheet_data([])
            self.sheet_gaso.headers([])
            return

        # Si db_manager devuelve dicts, usamos claves; si devuelve tuplas
        # sería necesario definir un orden; para simplificar, asumimos dicts.
        first = rows[0]
        if isinstance(first, dict):
            fields = [k for k in first.keys() if k != "id"]
            headers = [k for k in fields]
            data = [[r.get(f, "") for f in fields] for r in rows]
        else:
            # Si son tuplas, no sabemos el orden exacto -> mostramos tal cual
            headers = [f"C{i}" for i in range(len(first))]
            data = [list(t) for t in rows]

        self.sheet_gaso.set_sheet_data(
            data=data,
            reset_col_positions=True,
            reset_row_positions=True,
            redraw=True,
        )
        self.sheet_gaso.headers(headers)
        self.sheet_gaso.redraw()

    # ============================================================
    #   Orina
    # ============================================================
    def _refresh_orina(self):
        if not hasattr(self.db, "list_orina"):
            self.sheet_orina.set_sheet_data([])
            self.sheet_orina.headers([])
            return

        rows = self._get_rows_generic(
            list_method_name="list_orina",
            fallback_name=None,
            fields_order=self.ORINA_FIELDS,
        )

        if not rows:
            self.sheet_orina.set_sheet_data([])
            self.sheet_orina.headers([])
            return

        fields = self.ORINA_FIELDS[1:]  # sin id
        headers = [self.ORINA_HEADERS.get(f, f) for f in fields]

        data: List[List[Any]] = []
        for row in rows:
            data.append([row.get(f, "") for f in fields])

        self.sheet_orina.set_sheet_data(
            data=data,
            reset_col_positions=True,
            reset_row_positions=True,
            redraw=True,
        )
        self.sheet_orina.headers(headers)

        for i in range(len(headers)):
            if i == 0:
                self.sheet_orina.column_width(i, 110)
            else:
                self.sheet_orina.column_width(i, 90)

        self.sheet_orina.redraw()

    # ============================================================
    #   Utilidades comunes
    # ============================================================
    def _get_rows_generic(
        self,
        list_method_name: str,
        fallback_name: Optional[str],
        fields_order: List[str],
    ) -> List[Dict[str, Any]]:
        """
        Llama a db.<list_method_name>(limit=1000) o al fallback si existe,
        y convierte las filas a dicts con las claves de fields_order.
        Ordena por fecha_extraccion si existe.
        """
        if self.db is None:
            return []

        method = getattr(self.db, list_method_name, None)
        if method is None and fallback_name:
            method = getattr(self.db, fallback_name, None)

        if method is None:
            return []

        tuples_or_dicts = method(limit=1000)
        if not tuples_or_dicts:
            return []

        rows: List[Dict[str, Any]] = []

        first = tuples_or_dicts[0]
        if isinstance(first, dict):
            # Ya vienen como dicts
            for r in tuples_or_dicts:
                rows.append(dict(r))
        else:
            # Tuplas: las mapeamos usando fields_order
            for t in tuples_or_dicts:
                # Si el len no coincide, ignoramos
                if len(t) != len(fields_order):
                    continue
                row = {field: value for field, value in zip(fields_order, t)}
                rows.append(row)

        # Ordenar por fecha_extraccion si existe
        def parse_fecha(r: Dict[str, Any]):
            value = r.get("fecha_extraccion") or r.get("fecha_analisis") or ""
            if not value:
                return datetime.min
            try:
                return datetime.strptime(str(value), "%Y-%m-%d")
            except ValueError:
                return datetime.min

        rows.sort(key=parse_fecha)
        return rows

    def _apply_out_of_range_highlight(
        self,
        sheet: Sheet,
        rows: List[Dict[str, Any]],
        fields: List[str],
    ):
        """
        Aplica coloreado de celdas fuera de rango SOLO en la pestaña
        de Hematología (aunque técnicamente podría reutilizarse en otras).
        """
        if self.ranges_manager is None:
            return

        ranges = self.ranges_manager.get_all()

        for r_idx, row in enumerate(rows):
            for c_idx, field_name in enumerate(fields):
                if field_name not in ranges:
                    continue

                value = row.get(field_name)
                if self._is_out_of_range(field_name, value, ranges):
                    try:
                        sheet.highlight_cells(
                            row=r_idx,
                            column=c_idx,
                            bg="#ffdddd",
                            fg="red",
                            redraw=False,
                        )
                    except Exception:
                        pass

    def _is_out_of_range(
        self,
        field_name: str,
        value: Any,
        ranges: Dict[str, Any],
    ) -> bool:
        """
        Devuelve True si value está fuera de rango para field_name.
        """
        param = ranges.get(field_name)
        if not param:
            return False

        # Intentar convertir a float
        try:
            text = str(value).strip()
            if text == "":
                return False
            val = float(text.replace(",", "."))
        except (TypeError, ValueError):
            return False

        min_v = param.min_value
        max_v = param.max_value

        if min_v is not None and val < min_v:
            return True
        if max_v is not None and val > max_v:
            return True
        return False