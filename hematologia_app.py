# -*- coding: utf-8 -*-
"""
Aplicación de análisis de hematología
Autor: Borja Alonso Tristán
Año: 2025
"""

import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from pathlib import Path
import logging

from db_manager import HematologyDB
from pdf_to_json import parse_hematology_pdf
from analisis_view import AnalisisView
from charts_view import ChartsView
from ranges_config import RangesManager, RangesDialog


class HematologiaApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Análisis de Hematología")

        # Base de datos
        self.db = HematologyDB()
        self.current_db_path = None

        # Rangos
        self.ranges_manager = RangesManager()

        # Ventana centrada 1024x768
        w, h = 1024, 768
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        x, y = (sw - w) // 2, (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

        # Crear UI
        self._crear_menu()
        self._crear_contenido_inicial()
        self._actualizar_estado_menus()


    # ============================================================
    #   Menús
    # ============================================================
    def _crear_menu(self):
        menubar = tk.Menu(self)

        # --- ARCHIVO ---
        menu_archivo = tk.Menu(menubar, tearoff=0)
        menu_archivo.add_command(label="Nuevo Paciente (crear BD)...", command=self.nuevo_paciente)
        menu_archivo.add_command(label="Abrir datos de Paciente...", command=self.abrir_datos_paciente)
        menu_archivo.add_command(label="Cerrar datos del Paciente", command=self.cerrar_datos_paciente)
        menu_archivo.add_separator()
        menu_archivo.add_command(label="Salir", command=self.destroy)
        menubar.add_cascade(label="Archivo", menu=menu_archivo)

        # --- EDICIÓN ---
        self.menu_edicion = tk.Menu(menubar, tearoff=0)
        self.menu_edicion.add_command(label="Importar análisis desde PDF...", command=self.importar_analisis)
        menubar.add_cascade(label="Edición", menu=self.menu_edicion)

        # --- CONFIGURACIÓN ---
        menu_config = tk.Menu(menubar, tearoff=0)
        menu_config.add_command(label="Rangos de parámetros...", command=self.configurar_rangos)
        menubar.add_cascade(label="Configuración", menu=menu_config)

        # --- ACERCA DE ---
        menu_acerca = tk.Menu(menubar, tearoff=0)
        menu_acerca.add_command(label="Acerca de...", command=self.mostrar_acerca_de)
        menubar.add_cascade(label="Acerca de", menu=menu_acerca)

        self.config(menu=menubar)


    # ============================================================
    #   Contenido principal
    # ============================================================
    def _crear_contenido_inicial(self):
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)

        self.header_label = ttk.Label(
            container, text="Análisis de Hematología",
            font=("Segoe UI", 10)
        )
        self.header_label.pack(side="top", pady=10)

        # Paned vertical
        paned = ttk.PanedWindow(container, orient="vertical")
        paned.pack(fill="both", expand=True, padx=10, pady=10)

        top_frame = ttk.Frame(paned)
        bottom_frame = ttk.Frame(paned)

        paned.add(top_frame, weight=3)
        paned.add(bottom_frame, weight=2)

        # Tabla
        self.analisis_view = AnalisisView(
            top_frame, db=self.db, ranges_manager=self.ranges_manager
        )
        self.analisis_view.pack(fill="both", expand=True)

        # Gráficos
        self.charts_view = ChartsView(
            bottom_frame, db=self.db, ranges_manager=self.ranges_manager
        )
        self.charts_view.pack(fill="both", expand=True)

        self._update_patient_label()


    # ============================================================
    #   Archivo: crear/abrir/cerrar BD
    # ============================================================
    def nuevo_paciente(self):
        ruta = filedialog.asksaveasfilename(
            title="Crear nueva base de datos de Paciente",
            defaultextension=".db",
            filetypes=[("Bases SQLite", "*.db *.sqlite *.sqlite3")]
        )

        if not ruta:
            return

        try:
            self.db.create(ruta)
            self.current_db_path = ruta
            messagebox.showinfo("BD creada", f"Base de datos creada:\n{ruta}")
            self._post_db_open()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def abrir_datos_paciente(self):
        ruta = filedialog.askopenfilename(
            title="Abrir base de datos de Paciente",
            filetypes=[("Bases SQLite", "*.db *.sqlite *.sqlite3")]
        )

        if not ruta:
            return

        try:
            self.db.open(ruta)
            self.current_db_path = ruta
            messagebox.showinfo("BD abierta", f"Base de datos abierta:\n{ruta}")
            self._post_db_open()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def cerrar_datos_paciente(self):
        try:
            self.db.close()
            self.current_db_path = None
            self.analisis_view.clear()
            self.charts_view.clear()
            self._update_patient_label()
            self._actualizar_estado_menus()
            messagebox.showinfo("BD cerrada", "Se ha cerrado la base de datos.")
        except Exception:
            pass


    def _post_db_open(self):
        """Actualizar vistas tras abrir/crear una BD."""
        self.analisis_view.set_db(self.db)
        self.analisis_view.refresh()
        self.charts_view.set_db(self.db)
        self.charts_view.refresh()
        self._actualizar_estado_menus()
        self._update_patient_label()


    # ============================================================
    #   Importación desde PDF
    # ============================================================
    def _asegurar_bd_abierta(self) -> bool:
        if self.db is None or not self.db.is_open:
            messagebox.showwarning("Sin BD", "Antes debes abrir o crear una base de datos.")
            return False
        return True

    def importar_analisis(self):
        if not self._asegurar_bd_abierta():
            return

        rutas = filedialog.askopenfilenames(
            title="Seleccionar informes PDF",
            filetypes=[("PDF", "*.pdf")]
        )
        if not rutas:
            return

        errores = 0
        importados = 0

        for ruta in rutas:
            try:
                parsed = parse_hematology_pdf(ruta)

                # Guardar paciente
                if parsed.get("paciente"):
                    self.db.save_patient(parsed["paciente"])

                # Hematología
                for item in parsed.get("hematologia", []):
                    self.db.insert_hematologia(item)
                    importados += 1

                # Bioquímica
                for item in parsed.get("bioquimica", []):
                    self.db.insert_bioquimica(item)
                    importados += 1

                # Gasometría
                for item in parsed.get("gasometria", []):
                    self.db.insert_gasometria(item)
                    importados += 1

                # Orina
                for item in parsed.get("orina", []):
                    self.db.insert_orina(item)
                    importados += 1

            except Exception as e:
                errores += 1
                logging.error(f"Error importando {ruta}: {e}")

        self.analisis_view.refresh()
        self.charts_view.refresh()
        self._update_patient_label()

        if errores == 0:
            messagebox.showinfo("Importación completada", f"Importados {importados} análisis.")
        else:
            messagebox.showwarning(
                "Importación parcial",
                f"Importados {importados} análisis.\n{errores} PDF tuvieron errores."
            )


    # ============================================================
    #   Configuración de rangos
    # ============================================================
    def configurar_rangos(self):
        dlg = RangesDialog(self, self.ranges_manager)
        self.wait_window(dlg)

        self.analisis_view.set_ranges_manager(self.ranges_manager)
        self.charts_view.set_ranges_manager(self.ranges_manager)

        self.analisis_view.refresh()
        self.charts_view.refresh()


    # ============================================================
    #   Acerca de
    # ============================================================
    def mostrar_acerca_de(self):
        messagebox.showinfo(
            "Acerca de",
            "Aplicación de análisis de hematología\nAutor: Borja Alonso Tristán\nAño: 2025"
        )


    # ============================================================
    #   Auxiliares
    # ============================================================
    def _actualizar_estado_menus(self):
        estado = "normal" if (self.db and self.db.is_open) else "disabled"
        try:
            self.menu_edicion.entryconfig("Importar análisis desde PDF...", state=estado)
        except:
            pass

    def _update_patient_label(self):
        if not self.db or not self.db.is_open:
            self.header_label.config(text="Análisis de Hematología")
            return

        pac = self.db.get_patient()
        if not pac:
            self.header_label.config(text="Paciente: (sin datos)")
            return

        nombre = pac.get("nombre", "")
        apellidos = pac.get("apellidos", "")
        sexo = pac.get("sexo", "")
        nac = pac.get("fecha_nacimiento", "")
        hist = pac.get("numero_historia", "")

        linea1 = f"{nombre} {apellidos}".strip()
        linea2 = " | ".join(
            p for p in [
                f"Sexo: {sexo}" if sexo else None,
                f"Nac.: {nac}" if nac else None,
                f"Historia: {hist}" if hist else None,
            ] if p
        )

        self.header_label.config(
            text=f"{linea1}\n{linea2}",
            font=("Segoe UI", 10)
        )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler("hematologia.log", encoding="utf-8"),
            logging.StreamHandler()
        ]
    )
    app = HematologiaApp()
    app.mainloop()