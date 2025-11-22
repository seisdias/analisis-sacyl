# -*- coding: utf-8 -*-
"""
Configuración de rangos de parámetros de hematología.
Autor: Borja Alonso Tristán
Año: 2025
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, Optional, List
import tkinter as tk
from tkinter import ttk, messagebox


# -------------------------
#  MODELO DE DATOS
# -------------------------

@dataclass
class ParamRange:
    key: str           # nombre interno (coincide con la BD)
    label: str         # etiqueta visible
    category: str      # Serie blanca / Serie roja / Serie plaquetar
    unit: str          # unidades
    min_value: Optional[float]
    max_value: Optional[float]


# Rangos por defecto (adulto general)
DEFAULT_PARAM_RANGES: Dict[str, ParamRange] = {
    # SERIE BLANCA
    "leucocitos": ParamRange("leucocitos", "Leucocitos", "Serie blanca", "10³/µL", 4.0, 11.0),
    "neutrofilos_pct": ParamRange("neutrofilos_pct", "Neutrófilos %", "Serie blanca", "%", 40.0, 75.0),
    "linfocitos_pct": ParamRange("linfocitos_pct", "Linfocitos %", "Serie blanca", "%", 20.0, 45.0),
    "monocitos_pct": ParamRange("monocitos_pct", "Monocitos %", "Serie blanca", "%", 2.0, 10.0),
    "eosinofilos_pct": ParamRange("eosinofilos_pct", "Eosinófilos %", "Serie blanca", "%", 1.0, 6.0),
    "basofilos_pct": ParamRange("basofilos_pct", "Basófilos %", "Serie blanca", "%", 0.0, 2.0),

    "neutrofilos_abs": ParamRange("neutrofilos_abs", "Neutrófilos absolutos", "Serie blanca", "10³/µL", 1.5, 7.5),
    "linfocitos_abs": ParamRange("linfocitos_abs", "Linfocitos absolutos", "Serie blanca", "10³/µL", 1.0, 4.0),
    "monocitos_abs": ParamRange("monocitos_abs", "Monocitos absolutos", "Serie blanca", "10³/µL", 0.2, 1.0),
    "eosinofilos_abs": ParamRange("eosinofilos_abs", "Eosinófilos absolutos", "Serie blanca", "10³/µL", 0.0, 0.5),
    "basofilos_abs": ParamRange("basofilos_abs", "Basófilos absolutos", "Serie blanca", "10³/µL", 0.0, 0.2),

    # SERIE ROJA
    "hematies": ParamRange("hematies", "Hematíes", "Serie roja", "10⁶/µL", 4.0, 6.0),
    "hemoglobina": ParamRange("hemoglobina", "Hemoglobina", "Serie roja", "g/dL", 13.0, 17.5),
    "hematocrito": ParamRange("hematocrito", "Hematocrito", "Serie roja", "%", 40.0, 52.0),
    "vcm": ParamRange("vcm", "VCM", "Serie roja", "fL", 80.0, 100.0),
    "hcm": ParamRange("hcm", "HCM", "Serie roja", "pg", 27.0, 34.0),
    "chcm": ParamRange("chcm", "CHCM", "Serie roja", "g/dL", 32.0, 36.0),
    "rdw": ParamRange("rdw", "RDW", "Serie roja", "%", 11.0, 15.0),

    # SERIE PLAQUETAR
    "plaquetas": ParamRange("plaquetas", "Plaquetas", "Serie plaquetar", "10³/µL", 150.0, 450.0),
    "vpm": ParamRange("vpm", "VPM", "Serie plaquetar", "fL", 7.0, 12.0),
}


class RangesManager:
    """
    Mantiene los rangos actuales de los parámetros y permite
    restaurar los valores por defecto.
    """

    def __init__(self):
        # Copia independiente de los rangos por defecto
        self._ranges: Dict[str, ParamRange] = {
            key: ParamRange(**asdict(pr))
            for key, pr in DEFAULT_PARAM_RANGES.items()
        }

    def get_all(self) -> Dict[str, ParamRange]:
        return self._ranges

    def get_by_category(self) -> Dict[str, List[ParamRange]]:
        cats: Dict[str, List[ParamRange]] = {}
        for pr in self._ranges.values():
            cats.setdefault(pr.category, []).append(pr)
        # Ordenamos categorías y parámetros por label
        for cat in cats:
            cats[cat].sort(key=lambda r: r.label)
        return cats

    def update_range(self, key: str, min_value: Optional[float], max_value: Optional[float]) -> None:
        if key not in self._ranges:
            raise KeyError(f"Parámetro desconocido: {key}")
        pr = self._ranges[key]
        pr.min_value = min_value
        pr.max_value = max_value

    def reset_defaults(self) -> None:
        """
        Vuelve a cargar los rangos por defecto.
        """
        self._ranges = {
            key: ParamRange(**asdict(pr))
            for key, pr in DEFAULT_PARAM_RANGES.items()
        }


# -------------------------
#  DIÁLOGO DE CONFIGURACIÓN
# -------------------------

class RangesDialog(tk.Toplevel):
    """
    Popup con tabla-formulario para editar los rangos de parámetros.
    - Columnas: Parámetro, Mínimo, Máximo, Unidades.
    - Botones: Guardar, Cancelar, Restaurar valores por defecto.
    """

    def __init__(self, master, ranges_manager: RangesManager):
        super().__init__(master)
        self.title("Configuración de rangos de parámetros")
        self.ranges_manager = ranges_manager

        self.resizable(True, True)

        # Para restaurar en Cancelar, guardamos una copia local
        self._working_ranges: Dict[str, ParamRange] = {
            key: ParamRange(**asdict(pr))
            for key, pr in self.ranges_manager.get_all().items()
        }

        self._entries: Dict[str, Dict[str, tk.Entry]] = {}

        self._build_widgets()
        self._center_on_parent(master)

        # Modal
        self.transient(master)
        self.grab_set()
        self.wait_visibility()
        self.focus_set()

    def _center_on_parent(self, parent):
        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_x()
        py = parent.winfo_y()

        w = self.winfo_width()
        h = self.winfo_height()

        x = px + (pw // 2) - (w // 2)
        y = py + (ph // 2) - (h // 2)
        self.geometry(f"+{x}+{y}")

    def _build_widgets(self):
        # Frame principal
        main_frame = tk.Frame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Cabecera
        lbl = tk.Label(
            main_frame,
            text="Rangos de referencia para los parámetros de hematología",
            font=("Segoe UI", 11, "bold"),
            justify="left"
        )
        lbl.pack(anchor="w", pady=(0, 10))

        # Frame para la tabla
        table_frame = tk.Frame(main_frame)
        table_frame.pack(fill="both", expand=True)

        # Encabezados de la tabla
        header_frame = tk.Frame(table_frame)
        header_frame.grid(row=0, column=0, sticky="ew")
        tk.Label(header_frame, text="Parámetro", width=30, anchor="w").grid(row=0, column=0, padx=2)
        tk.Label(header_frame, text="Mínimo", width=10, anchor="center").grid(row=0, column=1, padx=2)
        tk.Label(header_frame, text="Máximo", width=10, anchor="center").grid(row=0, column=2, padx=2)
        tk.Label(header_frame, text="Unidad", width=10, anchor="w").grid(row=0, column=3, padx=2)

        # Frame con filas (podría hacerse scrollable si crece mucho)
        rows_frame = tk.Frame(table_frame)
        rows_frame.grid(row=1, column=0, sticky="nsew", pady=(5, 0))

        # Configurar el grid para expandir
        table_frame.grid_rowconfigure(1, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # Rellenar filas por categoría
        row_idx = 0
        by_cat = self._get_working_by_category()

        for cat_name in sorted(by_cat.keys()):
            # Fila de categoría
            cat_label = tk.Label(
                rows_frame,
                text=cat_name,
                font=("Segoe UI", 10, "bold")
            )
            cat_label.grid(row=row_idx, column=0, columnspan=4, sticky="w", pady=(8, 2))
            row_idx += 1

            for pr in by_cat[cat_name]:
                # Fila del parámetro
                desc = f"  • {pr.label}"
                tk.Label(rows_frame, text=desc, anchor="w").grid(row=row_idx, column=0, sticky="w", padx=2)

                entry_min = tk.Entry(rows_frame, width=10, justify="right")
                entry_max = tk.Entry(rows_frame, width=10, justify="right")

                if pr.min_value is not None:
                    entry_min.insert(0, f"{pr.min_value}")
                if pr.max_value is not None:
                    entry_max.insert(0, f"{pr.max_value}")

                entry_min.grid(row=row_idx, column=1, padx=2)
                entry_max.grid(row=row_idx, column=2, padx=2)

                tk.Label(rows_frame, text=pr.unit, anchor="w").grid(row=row_idx, column=3, sticky="w", padx=2)

                self._entries.setdefault(pr.key, {})["min"] = entry_min
                self._entries.setdefault(pr.key, {})["max"] = entry_max

                row_idx += 1

        # Botones
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=(10, 0))

        btn_cancelar = tk.Button(btn_frame, text="Cancelar", command=self._on_cancelar)
        btn_cancelar.pack(side="right", padx=5)

        btn_guardar = tk.Button(btn_frame, text="Guardar", command=self._on_guardar)
        btn_guardar.pack(side="right", padx=5)

        btn_restaurar = tk.Button(btn_frame, text="Restaurar valores por defecto", command=self._on_restaurar)
        btn_restaurar.pack(side="left", padx=5)

    def _get_working_by_category(self) -> Dict[str, List[ParamRange]]:
        cats: Dict[str, List[ParamRange]] = {}
        for pr in self._working_ranges.values():
            cats.setdefault(pr.category, []).append(pr)
        for cat in cats:
            cats[cat].sort(key=lambda r: r.label)
        return cats

    # -------------------------
    #  Acciones botones
    # -------------------------
    def _on_cancelar(self):
        # No copiamos nada al manager -> se quedan como estaban
        self.destroy()

    def _on_restaurar(self):
        resp = messagebox.askyesno(
            "Restaurar valores",
            "Se restaurarán los valores de rango por defecto para todos los parámetros.\n\n"
            "¿Deseas continuar?"
        )
        if not resp:
            return

        # Reponer working_ranges desde DEFAULT_PARAM_RANGES
        self._working_ranges = {
            key: ParamRange(**asdict(pr))
            for key, pr in DEFAULT_PARAM_RANGES.items()
        }

        # Refrescar entradas
        for key, widgets in self._entries.items():
            pr = self._working_ranges[key]
            e_min = widgets["min"]
            e_max = widgets["max"]
            e_min.delete(0, tk.END)
            e_max.delete(0, tk.END)
            if pr.min_value is not None:
                e_min.insert(0, f"{pr.min_value}")
            if pr.max_value is not None:
                e_max.insert(0, f"{pr.max_value}")

    def _on_guardar(self):
        """
        Valida y aplica los cambios al RangesManager.
        """
        # Validar todas las entradas
        for key, widgets in self._entries.items():
            e_min = widgets["min"]
            e_max = widgets["max"]

            txt_min = e_min.get().strip()
            txt_max = e_max.get().strip()

            min_val: Optional[float]
            max_val: Optional[float]

            if txt_min == "":
                min_val = None
            else:
                try:
                    min_val = float(txt_min.replace(",", "."))
                except ValueError:
                    messagebox.showerror(
                        "Valor no válido",
                        f"El valor mínimo para '{key}' no es un número válido."
                    )
                    e_min.focus_set()
                    return

            if txt_max == "":
                max_val = None
            else:
                try:
                    max_val = float(txt_max.replace(",", "."))
                except ValueError:
                    messagebox.showerror(
                        "Valor no válido",
                        f"El valor máximo para '{key}' no es un número válido."
                    )
                    e_max.focus_set()
                    return

            # Coherencia min <= max (si ambos existen)
            if min_val is not None and max_val is not None and min_val > max_val:
                messagebox.showerror(
                    "Rango inconsistente",
                    f"Para '{key}', el mínimo ({min_val}) es mayor que el máximo ({max_val})."
                )
                e_min.focus_set()
                return

            # Actualizar en working_ranges
            pr = self._working_ranges[key]
            pr.min_value = min_val
            pr.max_value = max_val

        # Si todo es válido, volcamos al manager real
        for key, pr in self._working_ranges.items():
            self.ranges_manager.update_range(key, pr.min_value, pr.max_value)

        self.destroy()
