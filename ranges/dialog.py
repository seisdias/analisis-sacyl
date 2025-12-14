# ranges/dialog.py
from __future__ import annotations
from dataclasses import asdict
from typing import Dict, List
import tkinter as tk
from tkinter import messagebox

from .models import ParamRange
from .defaults import DEFAULT_PARAM_RANGES
from .manager import RangesManager

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
