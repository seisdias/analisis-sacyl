# -*- coding: utf-8 -*-
"""
Aplicación principal de gestión de análisis de laboratorio.

Estructura:
 - Menú Archivo: nuevo / abrir / cerrar / salir
 - Menú Edición: importar análisis desde uno o varios PDF
 - Menú Configuración: rangos de referencia

Series soportadas:
 - Hematología (hemograma)
 - Bioquímica
 - Gasometría
 - Orina

Autor: Borja Alonso Tristán
Año: 2025
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional

from db_manager import HematologyDB
from analisis_view import AnalisisView
from charts_view import ChartsView
from ranges_config import RangesManager, RangesDialog
from lab_pdf  import parse_hematology_pdf


class HematologiaApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Gestor de análisis clínicos – Hematología / Bioquímica / Orina / Gasometría")
        self.geometry("1200x800")

        # Estado BD
        self.db: Optional[HematologyDB] = None
        self.db_path: Optional[str] = None

        # Rangos de referencia
        self.ranges_manager = RangesManager()

        # Construcción interfaz
        self._build_menu()
        self._build_main_layout()

    # ---------------------------------------------------------------------
    #   MENÚ
    # ---------------------------------------------------------------------
    def _build_menu(self):
        menubar = tk.Menu(self)

        # ---- Menú Archivo ----
        m_file = tk.Menu(menubar, tearoff=0)
        m_file.add_command(label="Nuevo paciente...", command=self.menu_new_db)
        m_file.add_command(label="Abrir datos paciente...", command=self.menu_open_db)
        m_file.add_separator()
        m_file.add_command(label="Cerrar datos", command=self.menu_close_db)
        m_file.add_separator()
        m_file.add_command(label="Cerrar aplicación", command=self.quit)
        menubar.add_cascade(label="Archivo", menu=m_file)

        # ---- Menú Edición ----
        m_edit = tk.Menu(menubar, tearoff=0)
        m_edit.add_command(
            label="Importar análisis desde PDF...",
            command=self.menu_import_pdfs
        )
        self.menu_edicion = m_edit
        menubar.add_cascade(label="Edición", menu=m_edit)

        # ---- Menú Configuración ----
        m_cfg = tk.Menu(menubar, tearoff=0)
        m_cfg.add_command(label="Rangos de parámetros...", command=self.menu_edit_ranges)
        menubar.add_cascade(label="Configuración", menu=m_cfg)

        self.config(menu=menubar)
        self._update_menus_state()

    # ---------------------------------------------------------------------
    #   LAYOUT PRINCIPAL
    # ---------------------------------------------------------------------
    def _build_main_layout(self):
        # Notebook con dos pestañas: Datos / Gráficas
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        self.tab_datos = ttk.Frame(self.notebook)
        self.tab_graficas = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_datos, text="Datos")
        self.notebook.add(self.tab_graficas, text="Gráficas")

        # Vista de datos
        self.analisis_view = AnalisisView(
            self.tab_datos,
            db=None,
            ranges_manager=self.ranges_manager,
        )
        self.analisis_view.pack(fill="both", expand=True)

        # Vista de gráficas
        self.charts_view = ChartsView(
            self.tab_graficas,
            db=None,
            ranges_manager=self.ranges_manager,
        )
        self.charts_view.pack(fill="both", expand=True)

    # ---------------------------------------------------------------------
    #   UTILIDAD: ACTUALIZAR ESTADO DE MENÚS
    # ---------------------------------------------------------------------
    def _db_is_open(self) -> bool:
        return self.db is not None and self.db.is_open

    def _update_menus_state(self):
        """Activa/desactiva opciones según haya BD abierta o no."""
        state = "normal" if self._db_is_open() else "disabled"
        try:
            self.menu_edicion.entryconfig("Importar análisis desde PDF...", state=state)
        except Exception:
            pass

    # ---------------------------------------------------------------------
    #   MENÚ ARCHIVO: NUEVO / ABRIR / CERRAR
    # ---------------------------------------------------------------------
    def menu_new_db(self):
        path = filedialog.asksaveasfilename(
            title="Crear nueva base de datos de paciente",
            defaultextension=".db",
            filetypes=[("Bases de datos SQLite", "*.db *.sqlite *.sqlite3"),
                       ("Todos los archivos", "*.*")]
        )
        if not path:
            return

        if os.path.exists(path):
            resp = messagebox.askyesno(
                "Sobrescribir base de datos",
                f"El archivo '{path}' ya existe.\n\n"
                "¿Deseas reemplazarlo por una nueva base de datos vacía?"
            )
            if not resp:
                return
            os.remove(path)

        # Crear nueva BD
        self.db = HematologyDB(path)
        self.db_path = path
        self.db.open()

        messagebox.showinfo(
            "Base de datos creada",
            f"Se ha creado la base de datos:\n{path}"
        )

        self.refresh_all()
        self._update_menus_state()

    def menu_open_db(self):
        path = filedialog.askopenfilename(
            title="Abrir base de datos de paciente",
            filetypes=[("Bases de datos SQLite", "*.db *.sqlite *.sqlite3"),
                       ("Todos los archivos", "*.*")]
        )
        if not path:
            return

        if not os.path.exists(path):
            messagebox.showerror(
                "Archivo no existente",
                f"El archivo '{path}' no existe."
            )
            return

        self.db = HematologyDB(path)
        self.db_path = path
        self.db.open()

        messagebox.showinfo(
            "Base de datos abierta",
            f"Se ha abierto la base de datos:\n{path}"
        )

        self.refresh_all()
        self._update_menus_state()

    def menu_close_db(self):
        if self.db:
            self.db.close()

        self.db = None
        self.db_path = None

        self.analisis_view.set_db(None)
        self.charts_view.set_db(None)
        self.analisis_view.clear()
        self.charts_view.clear()

        messagebox.showinfo(
            "Base de datos cerrada",
            "Se han cerrado los datos del paciente."
        )

        self._update_menus_state()

    # ---------------------------------------------------------------------
    #   MENÚ EDICIÓN: IMPORTAR PDF(S)
    # ---------------------------------------------------------------------
    def menu_import_pdfs(self):
        if not self._db_is_open():
            messagebox.showwarning(
                "Sin base de datos",
                "No hay base de datos abierta.\n\n"
                "Crea o abre una base de datos desde el menú 'Archivo'."
            )
            return

        rutas = filedialog.askopenfilenames(
            title="Seleccionar informes de laboratorio (PDF)",
            filetypes=[("Archivos PDF", "*.pdf")]
        )
        if not rutas:
            return

        ok_count = 0
        errores: list[str] = []

        for ruta in rutas:
            try:
                data = parse_hematology_pdf(ruta)

                # Paciente (si viene)
                if isinstance(data.get("paciente"), dict):
                    self.db.save_patient(data["paciente"])

                # Hematología
                for d in data.get("hematologia", []):
                    self.db.insert_hematologia(d)

                # Bioquímica
                for d in data.get("bioquimica", []):
                    self.db.insert_bioquimica(d)

                # Gasometría
                for d in data.get("gasometria", []):
                    self.db.insert_gasometria(d)

                # Orina
                for d in data.get("orina", []):
                    self.db.insert_orina(d)

                ok_count += 1

            except Exception as e:
                errores.append(f"{os.path.basename(ruta)}: {e}")

        # Refrescamos vistas una sola vez al final
        self.refresh_all()

        if errores and ok_count > 0:
            messagebox.showwarning(
                "Importación parcial",
                "Se importaron algunos informes, pero hubo errores:\n\n"
                + "\n".join(errores)
            )
        elif errores and ok_count == 0:
            messagebox.showerror(
                "Error en la importación",
                "No se pudo importar ningún informe:\n\n"
                + "\n".join(errores)
            )
        else:
            messagebox.showinfo(
                "Importación completada",
                f"Se importaron correctamente {ok_count} informe(s) de laboratorio."
            )

    # ---------------------------------------------------------------------
    #   MENÚ CONFIGURACIÓN: RANGOS
    # ---------------------------------------------------------------------
    def menu_edit_ranges(self):
        dlg = RangesDialog(self, self.ranges_manager)
        dlg.wait_window()
        # Al cerrar el diálogo, refrescamos vistas
        self.analisis_view.refresh()
        self.charts_view.refresh()

    # ---------------------------------------------------------------------
    #   REFRESCAR TODAS LAS VISTAS
    # ---------------------------------------------------------------------
    def refresh_all(self):
        if not self._db_is_open():
            return

        self.analisis_view.set_db(self.db)
        self.charts_view.set_db(self.db)

        self.analisis_view.refresh()
        self.charts_view.refresh()


if __name__ == "__main__":
    app = HematologiaApp()
    app.mainloop()