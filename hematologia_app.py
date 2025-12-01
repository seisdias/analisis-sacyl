# -*- coding: utf-8 -*-
"""
Aplicación principal de gestión de análisis de laboratorio.
Modelo A:
 - "Nuevo paciente": elegir archivo .db → crear (confirmar sobrescritura si existe)
 - "Abrir paciente": abrir archivo existente
 - "Cerrar": cerrar conexión
Autor: Borja Alonso Tristán
Año: 2025
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import json

from db_manager import HematologyDB
from analisis_view import AnalisisView
from charts_view import ChartsView
from ranges_config import RangesManager, RangesDialog
from pdf_to_json import parse_hematology_pdf


class HematologiaApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Gestor de análisis clínicos – Hematología / Bioquímica / Orina / Gasometría")
        self.geometry("1200x800")

        # DB
        self.db: HematologyDB | None = None
        self.db_path: str | None = None

        # Ranges
        self.ranges_manager = RangesManager()

        # UI
        self._build_menu()
        self._build_main_layout()

    # ---------------------------------------------------------------------
    #   INTERFAZ
    # ---------------------------------------------------------------------
    def _build_menu(self):
        menubar = tk.Menu(self)

        # --- Archivo ---
        m_file = tk.Menu(menubar, tearoff=0)
        m_file.add_command(label="Nuevo paciente...", command=self.menu_new_db)
        m_file.add_command(label="Abrir paciente...", command=self.menu_open_db)
        m_file.add_separator()
        m_file.add_command(label="Importar PDF de análisis...", command=self.menu_import_pdf)
        m_file.add_separator()
        m_file.add_command(label="Cerrar datos", command=self.menu_close_db)
        m_file.add_separator()
        m_file.add_command(label="Salir", command=self.quit)
        menubar.add_cascade(label="Archivo", menu=m_file)

        # --- Configuración ---
        m_cfg = tk.Menu(menubar, tearoff=0)
        m_cfg.add_command(label="Rangos de referencia...", command=self.menu_edit_ranges)
        menubar.add_cascade(label="Configuración", menu=m_cfg)

        self.config(menu=menubar)

    def _build_main_layout(self):
        # Notebook (dos pestañas)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        # Tab 1: Datos en tabla
        self.tab_datos = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_datos, text="Datos")

        # Tab 2: Gráficas
        self.tab_graficas = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_graficas, text="Gráficas")

        # Dentro de Datos → AnalisisView
        self.analisis_view = AnalisisView(
            self.tab_datos,
            db=None,
            ranges_manager=self.ranges_manager
        )
        self.analisis_view.pack(fill="both", expand=True)

        # Dentro de Gráficas → ChartsView
        self.charts_view = ChartsView(
            self.tab_graficas,
            db=None,
            ranges_manager=self.ranges_manager
        )
        self.charts_view.pack(fill="both", expand=True)

    # ---------------------------------------------------------------------
    #   MENÚ: NUEVO PACIENTE (CREAR BD)
    # ---------------------------------------------------------------------
    def menu_new_db(self):
        path = filedialog.asksaveasfilename(
            title="Crear nueva base de datos",
            defaultextension=".db",
            filetypes=[("Base de datos SQLite", "*.db")]
        )
        if not path:
            return

        if os.path.exists(path):
            if not messagebox.askyesno(
                "Sobrescribir",
                "El archivo ya existe.\n¿Deseas sobrescribirlo completamente?"
            ):
                return
            os.remove(path)

        self.db = HematologyDB(path)
        self.db_path = path
        self.db.open()

        messagebox.showinfo("Nueva BD", "Base de datos creada correctamente.")
        self.refresh_all()

    # ---------------------------------------------------------------------
    #   MENÚ: ABRIR BD EXISTENTE
    # ---------------------------------------------------------------------
    def menu_open_db(self):
        path = filedialog.askopenfilename(
            title="Abrir base de datos",
            filetypes=[("Base de datos SQLite", "*.db")]
        )
        if not path:
            return

        if not os.path.exists(path):
            messagebox.showerror("Error", "El archivo no existe.")
            return

        self.db = HematologyDB(path)
        self.db_path = path
        self.db.open()

        messagebox.showinfo("BD abierta", f"Archivo cargado:\n{path}")
        self.refresh_all()

    # ---------------------------------------------------------------------
    #   MENÚ: IMPORTAR PDF
    # ---------------------------------------------------------------------
    def menu_import_pdf(self):
        if not self.db:
            messagebox.showerror("Sin BD", "Debes crear o abrir una base de datos primero.")
            return

        pdf_path = filedialog.askopenfilename(
            title="Seleccionar PDF de análisis",
            filetypes=[("PDF", "*.pdf")]
        )
        if not pdf_path:
            return

        try:
            data = parse_hematology_pdf(pdf_path)
        except Exception as e:
            messagebox.showerror("Error al importar PDF", str(e))
            return

        # -----------------------------------------
        # Guardar datos de paciente
        # -----------------------------------------
        if "paciente" in data:
            self.db.save_patient(data["paciente"])

        # -----------------------------------------
        # Insertar todas las series del análisis
        # -----------------------------------------
        if "hematologia" in data:
            for d in data["hematologia"]:
                self.db.insert_hematologia(d)

        if "bioquimica" in data:
            for d in data["bioquimica"]:
                self.db.insert_bioquimica(d)

        if "gasometria" in data:
            for d in data["gasometria"]:
                self.db.insert_gasometria(d)

        if "orina" in data:
            for d in data["orina"]:
                self.db.insert_orina(d)

        messagebox.showinfo("Importación completada", "PDF importado correctamente.")
        self.refresh_all()

    # ---------------------------------------------------------------------
    #   MENÚ: CERRAR BD
    # ---------------------------------------------------------------------
    def menu_close_db(self):
        if self.db:
            self.db.close()

        self.db = None
        self.db_path = None
        self.analisis_view.set_db(None)
        self.charts_view.set_db(None)

        self.analisis_view.clear()
        self.charts_view.clear()

        messagebox.showinfo("Cerrado", "Base de datos cerrada.")

    # ---------------------------------------------------------------------
    #   MENÚ: EDITAR RANGOS
    # ---------------------------------------------------------------------
    def menu_edit_ranges(self):
        dlg = RangesDialog(self, self.ranges_manager)
        dlg.wait_window()
        # actualizar vistas
        self.analisis_view.refresh()
        self.charts_view.refresh()

    # ---------------------------------------------------------------------
    #   REFRESCAR PANTALLAS
    # ---------------------------------------------------------------------
    def refresh_all(self):
        if not self.db:
            return

        self.analisis_view.set_db(self.db)
        self.charts_view.set_db(self.db)

        self.analisis_view.refresh()
        self.charts_view.refresh()


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    app = HematologiaApp()
    app.mainloop()