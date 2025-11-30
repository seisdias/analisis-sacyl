# -*- coding: utf-8 -*-
"""
Configuración de rangos de parámetros de laboratorio:
hematología, bioquímica y orina.
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
    category: str      # grupo (Serie blanca, Bioquímica básica, Orina, ...)
    unit: str          # unidades
    min_value: Optional[float]
    max_value: Optional[float]


# -------------------------
#  RANGOS POR DEFECTO
# -------------------------

DEFAULT_PARAM_RANGES: Dict[str, ParamRange] = {
    # ======= BIOQUÍMICA BÁSICA =======
    "glucosa": ParamRange(
        "glucosa", "Glucosa", "Bioquímica — Metabolismo", "mg/dL", 70.0, 110.0
    ),
    "urea": ParamRange(
        "urea", "Urea", "Bioquímica — Metabolismo", "mg/dL", 15.0, 50.0
    ),
    "creatinina": ParamRange(
        "creatinina", "Creatinina", "Bioquímica — Metabolismo", "mg/dL", 0.6, 1.3
    ),

    # ======= ELECTROLITOS / IONES =======
    "calcio": ParamRange(
        "calcio", "Calcio", "Bioquímica — Electrolitos", "mg/dL", 8.4, 10.2
    ),
    "cloro": ParamRange(
        "cloro", "Cloro", "Bioquímica — Electrolitos", "mmol/L", 97.0, 109.0
    ),
    "fosforo": ParamRange(
        "fosforo", "Fósforo", "Bioquímica — Electrolitos", "mg/dL", 2.5, 4.9
    ),
    "potasio": ParamRange(
        "potasio", "Potasio", "Bioquímica — Electrolitos", "mmol/L", 3.5, 5.1
    ),
    "sodio": ParamRange(
        "sodio", "Sodio", "Bioquímica — Electrolitos", "mmol/L", 136.0, 146.0
    ),

    # ======= PERFIL LIPÍDICO =======
    "colesterol_total": ParamRange(
        "colesterol_total", "Colesterol total", "Bioquímica — Lípidos", "mg/dL", 0.0, 200.0
    ),
    "colesterol_hdl": ParamRange(
        "colesterol_hdl", "Colesterol HDL", "Bioquímica — Lípidos", "mg/dL", 40.0, 80.0
    ),
    "colesterol_ldl": ParamRange(
        "colesterol_ldl", "Colesterol LDL", "Bioquímica — Lípidos", "mg/dL", 0.0, 130.0
    ),
    "colesterol_no_hdl": ParamRange(
        "colesterol_no_hdl", "Colesterol no HDL", "Bioquímica — Lípidos", "mg/dL", 0.0, 160.0
    ),
    "trigliceridos": ParamRange(
        "trigliceridos", "Triglicéridos", "Bioquímica — Lípidos", "mg/dL", 0.0, 150.0
    ),
    "indice_riesgo": ParamRange(
        "indice_riesgo", "Índice riesgo", "Bioquímica — Lípidos", "", 0.0, 5.0
    ),

    # ======= HIERRO / VITAMINAS =======
    "hierro": ParamRange(
        "hierro", "Hierro", "Bioquímica — Metabolismo hierro", "µg/dL", 60.0, 170.0
    ),
    "ferritina": ParamRange(
        "ferritina", "Ferritina", "Bioquímica — Metabolismo hierro", "ng/mL", 30.0, 400.0
    ),
    "vitamina_b12": ParamRange(
        "vitamina_b12", "Vitamina B12", "Bioquímica — Vitaminas", "pg/mL", 200.0, 900.0
    ),

    # ======= HEMATOLOGÍA — SERIE BLANCA =======
    "leucocitos": ParamRange(
        "leucocitos", "Leucocitos", "Hematología — Serie blanca", "10³/µL", 4.0, 11.0
    ),
    "neutrofilos_pct": ParamRange(
        "neutrofilos_pct", "Neutrófilos %", "Hematología — Serie blanca", "%", 40.0, 75.0
    ),
    "linfocitos_pct": ParamRange(
        "linfocitos_pct", "Linfocitos %", "Hematología — Serie blanca", "%", 20.0, 45.0
    ),
    "monocitos_pct": ParamRange(
        "monocitos_pct", "Monocitos %", "Hematología — Serie blanca", "%", 2.0, 10.0
    ),
    "eosinofilos_pct": ParamRange(
        "eosinofilos_pct", "Eosinófilos %", "Hematología — Serie blanca", "%", 1.0, 6.0
    ),
    "basofilos_pct": ParamRange(
        "basofilos_pct", "Basófilos %", "Hematología — Serie blanca", "%", 0.0, 2.0
    ),

    "neutrofilos_abs": ParamRange(
        "neutrofilos_abs", "Neutrófilos abs", "Hematología — Serie blanca", "10³/µL", 1.5, 7.5
    ),
    "linfocitos_abs": ParamRange(
        "linfocitos_abs", "Linfocitos abs", "Hematología — Serie blanca", "10³/µL", 1.0, 4.0
    ),
    "monocitos_abs": ParamRange(
        "monocitos_abs", "Monocitos abs", "Hematología — Serie blanca", "10³/µL", 0.2, 1.0
    ),
    "eosinofilos_abs": ParamRange(
        "eosinofilos_abs", "Eosinófilos abs", "Hematología — Serie blanca", "10³/µL", 0.0, 0.5
    ),
    "basofilos_abs": ParamRange(
        "basofilos_abs", "Basófilos abs", "Hematología — Serie blanca", "10³/µL", 0.0, 0.2
    ),

    # ======= HEMATOLOGÍA — SERIE ROJA =======
    "hematies": ParamRange(
        "hematies", "Hematíes", "Hematología — Serie roja", "10⁶/µL", 4.0, 6.0
    ),
    "hemoglobina": ParamRange(
        "hemoglobina", "Hemoglobina", "Hematología — Serie roja", "g/dL", 13.0, 17.5
    ),
    "hematocrito": ParamRange(
        "hematocrito", "Hematocrito", "Hematología — Serie roja", "%", 40.0, 52.0
    ),
    "vcm": ParamRange(
        "vcm", "VCM", "Hematología — Serie roja", "fL", 80.0, 100.0
    ),
    "hcm": ParamRange(
        "hcm", "HCM", "Hematología — Serie roja", "pg", 27.0, 34.0
    ),
    "chcm": ParamRange(
        "chcm", "CHCM", "Hematología — Serie roja", "g/dL", 32.0, 36.0
    ),
    "rdw": ParamRange(
        "rdw", "RDW", "Hematología — Serie roja", "%", 11.0, 15.0
    ),

    # ======= HEMATOLOGÍA — SERIE PLAQUETAR =======
    "plaquetas": ParamRange(
        "plaquetas", "Plaquetas", "Hematología — Serie plaquetar", "10³/µL", 150.0, 450.0
    ),
    "vpm": ParamRange(
        "vpm", "VPM", "Hematología — Serie plaquetar", "fL", 7.0, 12.0
    ),

    # ======= ORINA — CUANTITATIVA =======
    "albumina_ur": ParamRange(
        "albumina_ur", "Albúmina orina", "Orina — Cuantitativa", "mg/L", 0.0, 30.0
    ),
    "creatinina_ur": ParamRange(
        "creatinina_ur", "Creatinina orina", "Orina — Cuantitativa", "mg/dL", 20.0, 300.0
    ),
    "densidad": ParamRange(
        "densidad", "Densidad", "Orina — Cuantitativa", "", 1.005, 1.03
    ),
    "sodio_ur": ParamRange(
        "sodio_ur", "Sodio orina", "Orina — Cuantitativa", "mmol/L", 40.0, 220.0
    ),
    "ph": ParamRange(
        "ph", "pH orina", "Orina — Cuantitativa", "", 5.0, 8.0
    ),
    "indice_albumina_creatinina": ParamRange(
        "indice_albumina_creatinina", "Índice Alb/Cre", "Orina — Cuantitativa", "mg/g", 0.0, 30.0
    ),
}


# -------------------------
#  GESTOR DE RANGOS
# -------------------------

class RangesManager:
    """
    Mantiene los rangos actuales de los parámetros y permite
    restaurar los valores por defecto.
    """

    def __init__(self):
        self.reset_defaults()

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
    Incluye scroll vertical para que siempre se vean todos los campos,
    y los botones quedan fijos en la parte inferior.
    """

    def __init__(self, master, ranges_manager: RangesManager):
        super().__init__(master)
        self.title("Configuración de rangos de laboratorio")
        self.ranges_manager = ranges_manager

        # Copia de trabajo (para cancelar sin aplicar)
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

    # ---------- Layout y scroll ----------

    def _build_widgets(self):
        self.geometry("720x600")
        self.minsize(640, 480)

        main_frame = tk.Frame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        main_frame.rowconfigure(1, weight=1)
        main_frame.columnconfigure(0, weight=1)

        # Cabecera
        lbl = tk.Label(
            main_frame,
            text="Rangos de referencia (hematología, bioquímica y orina)",
            font=("Segoe UI", 11, "bold"),
            justify="left",
        )
        lbl.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

        # --- Área scrollable ---
        canvas = tk.Canvas(main_frame, borderwidth=0, highlightthickness=0)
        vscroll = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vscroll.set)

        canvas.grid(row=1, column=0, sticky="nsew")
        vscroll.grid(row=1, column=1, sticky="ns")

        self._rows_container = tk.Frame(canvas)
        canvas_window = canvas.create_window((0, 0), window=self._rows_container, anchor="nw")

        def _on_frame_configure(_event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _on_canvas_configure(event):
            # Que el frame interior tenga siempre el mismo ancho que el canvas
            canvas.itemconfig(canvas_window, width=event.width)

        self._rows_container.bind("<Configure>", _on_frame_configure)
        canvas.bind("<Configure>", _on_canvas_configure)

        # ---- Cabecera de columnas dentro del área scrollable ----
        header_frame = tk.Frame(self._rows_container)
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.columnconfigure(0, weight=1)

        tk.Label(header_frame, text="Parámetro", width=30, anchor="w").grid(row=0, column=0, padx=2)
        tk.Label(header_frame, text="Min", width=10, anchor="center").grid(row=0, column=1, padx=2)
        tk.Label(header_frame, text="Max", width=10, anchor="center").grid(row=0, column=2, padx=2)
        tk.Label(header_frame, text="Unidades", width=10, anchor="w").grid(row=0, column=3, padx=2)

        rows_frame = tk.Frame(self._rows_container)
        rows_frame.grid(row=1, column=0, sticky="nsew", pady=(5, 0))

        # Rellenar filas por categoría
        row_idx = 0
        by_cat = self._get_working_by_category()

        for cat_name in sorted(by_cat.keys()):
            # Fila de categoría
            cat_label = tk.Label(
                rows_frame,
                text=cat_name,
                font=("Segoe UI", 10, "bold"),
            )
            cat_label.grid(row=row_idx, column=0, columnspan=4, sticky="w", pady=(8, 2))
            row_idx += 1

            for pr in by_cat[cat_name]:
                desc = f"  • {pr.label}"
                tk.Label(rows_frame, text=desc, anchor="w").grid(
                    row=row_idx, column=0, sticky="w", padx=2
                )

                entry_min = tk.Entry(rows_frame, width=10, justify="right")
                entry_max = tk.Entry(rows_frame, width=10, justify="right")

                if pr.min_value is not None:
                    entry_min.insert(0, f"{pr.min_value}")
                if pr.max_value is not None:
                    entry_max.insert(0, f"{pr.max_value}")

                entry_min.grid(row=row_idx, column=1, padx=2)
                entry_max.grid(row=row_idx, column=2, padx=2)

                tk.Label(rows_frame, text=pr.unit, anchor="w").grid(
                    row=row_idx, column=3, sticky="w", padx=2
                )

                self._entries.setdefault(pr.key, {})["min"] = entry_min
                self._entries.setdefault(pr.key, {})["max"] = entry_max

                row_idx += 1

        # --- Botones fijos abajo ---
        btn_frame = tk.Frame(main_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)
        btn_frame.columnconfigure(2, weight=1)

        btn_restaurar = tk.Button(
            btn_frame,
            text="Restaurar valores por defecto",
            command=self._on_restaurar,
        )
        btn_restaurar.grid(row=0, column=0, sticky="w", padx=5)

        btn_cancelar = tk.Button(btn_frame, text="Cancelar", command=self._on_cancelar)
        btn_cancelar.grid(row=0, column=1, sticky="e", padx=5)

        btn_guardar = tk.Button(btn_frame, text="Guardar", command=self._on_guardar)
        btn_guardar.grid(row=0, column=2, sticky="e", padx=5)

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
            "¿Deseas continuar?",
        )
        if not resp:
            return

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
        for key, widgets in self._entries.items():
            e_min = widgets["min"]
            e_max = widgets["max"]

            txt_min = e_min.get().strip()
            txt_max = e_max.get().strip()

            if txt_min == "":
                min_val = None
            else:
                try:
                    min_val = float(txt_min.replace(",", "."))
                except ValueError:
                    messagebox.showerror(
                        "Valor no válido",
                        f"El valor mínimo para '{key}' no es un número válido.",
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
                        f"El valor máximo para '{key}' no es un número válido.",
                    )
                    e_max.focus_set()
                    return

            if (
                min_val is not None
                and max_val is not None
                and min_val > max_val
            ):
                messagebox.showerror(
                    "Rango inconsistente",
                    f"Para '{key}', el mínimo ({min_val}) es mayor que el máximo ({max_val}).",
                )
                e_min.focus_set()
                return

            pr = self._working_ranges[key]
            pr.min_value = min_val
            pr.max_value = max_val

        # Volcamos al manager real
        for key, pr in self._working_ranges.items():
            self.ranges_manager.update_range(key, pr.min_value, pr.max_value)

        self.destroy()