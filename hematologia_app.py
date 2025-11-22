# -*- coding: utf-8 -*-
"""
Aplicación de análisis de hematología
Autor: Borja Alonso Tristán
Año: 2025
"""

import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from db_manager import HematologyDB
from pdf_to_json import parse_hematology_pdf
from analisis_view import AnalisisView
from charts_view import ChartsView
from ranges_config import RangesManager, RangesDialog
import logging


class HematologiaApp(tk.Tk):
    def __init__(self):
        super().__init__()

        # --- Configuración básica de la ventana ---
        self.title("Análisis de Hematología")

        # --- Gestor de base de datos ---
        self.db = HematologyDB()
        self.ruta_bd = None

        # --- Gestor de rangos de parámetros ---
        self.ranges_manager = RangesManager()

        # Dimensiones recomendadas: 1024x768 y centrada
        ancho = 1024
        alto = 768

        # Obtener tamaño de la pantalla
        pantalla_ancho = self.winfo_screenwidth()
        pantalla_alto = self.winfo_screenheight()

        # Calcular posición centrada
        x = (pantalla_ancho // 2) - (ancho // 2)
        y = (pantalla_alto // 2) - (alto // 2)

        # Establecer tamaño y posición
        self.geometry(f"{ancho}x{alto}+{x}+{y}")

        # Crear menús
        self._crear_menu()

        # Aquí podríamos añadir widgets principales más adelante
        self._crear_contenido_inicial()
        self._actualizar_estado_menus()

    def _crear_menu(self):
        menubar = tk.Menu(self)

        # --- Menú Archivo ---
        menu_archivo = tk.Menu(menubar, tearoff=0)

        menu_archivo.add_command(
            label="Nuevo Paciente...",
            command=self.nuevo_paciente
        )
        menu_archivo.add_command(
            label="Abrir Datos Paciente...",
            command=self.abrir_datos_paciente
        )
        menu_archivo.add_command(
            label="Cerrar datos Paciente",
            command=self.cerrar_datos_paciente
        )
        menu_archivo.add_separator()
        menu_archivo.add_command(
            label="Cerrar aplicación",
            command=self.cerrar_aplicacion
        )
        menubar.add_cascade(label="Archivo", menu=menu_archivo)

        # --- Menú Edición ---
        self.menu_edicion = tk.Menu(menubar, tearoff=0)  # ⬅️ AHORA ES self.menu_edicion
        self.menu_edicion.add_command(
            label="Importar análisis desde PDF...",       # ⬅️ Texto alineado con _actualizar_estado_menus
            command=self.importar_analisis
        )
        menubar.add_cascade(label="Edición", menu=self.menu_edicion)

        # --- Menú Configuración ---
        menu_config = tk.Menu(menubar, tearoff=0)
        menu_config.add_command(
            label="Rangos de parámetros...",
            command=self.configurar_rangos
        )
        menubar.add_cascade(label="Configuración", menu=menu_config)

        # --- Menú Acerca de ---
        menu_acerca = tk.Menu(menubar, tearoff=0)
        menu_acerca.add_command(
            label="Acerca de...",
            command=self.mostrar_acerca_de
        )
        menubar.add_cascade(label="Acerca de", menu=menu_acerca)

        # Asignar la barra de menús a la ventana
        self.config(menu=menubar)


    def _crear_contenido_inicial(self):
        # Contenedor principal
        container = tk.Frame(self)
        container.pack(fill="both", expand=True)

        etiqueta = tk.Label(
            container,
            text="Aplicación de análisis de hematología (Borja Alonso Tristán, 2025)",
            font=("Segoe UI", 10),
            justify="center"
        )
        etiqueta.pack(side="top", pady=10)

        # Paned vertical para separar tabla (arriba) y gráficas (abajo)
        paned = ttk.PanedWindow(container, orient="vertical")
        paned.pack(fill="both", expand=True, padx=10, pady=10)

        top_frame = ttk.Frame(paned)
        bottom_frame = ttk.Frame(paned)

        paned.add(top_frame, weight=3)   # más espacio a la tabla al inicio
        paned.add(bottom_frame, weight=2)

        # --- Vista de análisis (tabla) ---
        self.analisis_view = AnalisisView(
            top_frame,
            db=self.db,
            ranges_manager=self.ranges_manager,
            borderwidth=1,
            relief="sunken"
        )
        self.analisis_view.pack(fill="both", expand=True)

        # --- Panel de gráficas ---
        self.charts_view = ChartsView(
            bottom_frame,
            db=self.db,
            ranges_manager=self.ranges_manager
        )
        self.charts_view.pack(fill="both", expand=True)



    # ==========================
    #   MÉTODOS DEL MENÚ ARCHIVO
    # ==========================
    def nuevo_paciente(self):
        """
        Crea una NUEVA base de datos SQLite.
        Si ya existe el archivo elegido, preguntamos si se sobrescribe.
        """
        ruta = filedialog.asksaveasfilename(
            title="Crear nueva base de datos de Paciente",
            defaultextension=".db",
            filetypes=[
                ("Bases de datos SQLite", "*.db *.sqlite *.sqlite3"),
                ("Todos los archivos", "*.*")
            ]
        )
        if not ruta:
            return

        try:
            # Si existe, preguntamos
            from pathlib import Path
            db_path = Path(ruta)
            overwrite = False
            if db_path.exists():
                resp = messagebox.askyesno(
                    "Sobrescribir base de datos de Paciente",
                    f"El archivo '{ruta}' ya existe.\n\n"
                    "¿Deseas reemplazarlo por una nueva base de datos de Paciente vacía?"
                )
                if not resp:
                    return
                overwrite = True

            # Crear nueva BD
            self.db.create_new(ruta, overwrite=overwrite)
            self.ruta_bd = ruta

            messagebox.showinfo(
                "Base de datos Paciente creada",
                f"Se ha creado la nueva base de datos de Paciente:\n{ruta}"
            )

            # Actualizar vista central y menús
            self.analisis_view.set_db(self.db)
            self.analisis_view.refresh()
            self.charts_view.set_db(self.db)
            self.charts_view.refresh()
            self._actualizar_estado_menus()

        except Exception as e:
            messagebox.showerror(
                "Error al crear la base de datos",
                f"No se ha podido crear la base de datos de Paciente:\n{ruta}\n\n"
                f"Detalle del error:\n{e}"
            )

    def abrir_datos_paciente(self):
        """
        Abre una base de datos ya existente.
        Si no existe, se muestra error (no se crea nueva aquí).
        """
        ruta = filedialog.askopenfilename(
            title="Abrir base de datos de Paciente existente",
            filetypes=[
                ("Bases de datos SQLite", "*.db *.sqlite *.sqlite3"),
                ("Todos los archivos", "*.*")
            ]
        )
        if not ruta:
            return

        try:
            self.db.open_existing(ruta)
            self.ruta_bd = ruta
            messagebox.showinfo(
                "Base de datos de Paciente abierta",
                f"Se ha abierto la base de datos de Paciente:\n{ruta}"
            )
            
            # Actualizar vista central y menús
            self.analisis_view.set_db(self.db)
            self.analisis_view.refresh()
            self.charts_view.set_db(self.db)
            self.charts_view.refresh()
            self._actualizar_estado_menus()

        except FileNotFoundError as e:
            messagebox.showerror(
                "Base de datos de Paciente no encontrada",
                str(e)
            )
        except Exception as e:
            messagebox.showerror(
                "Error al abrir la base de datos de Paciente",
                f"No se ha podido abrir la base de datos de Paciente:\n{ruta}\n\n"
                f"Detalle del error:\n{e}"
            )

    def cerrar_datos_paciente(self):
        """
        Cierra la base de datos actualmente abierta.
        """
        if self.db is not None and self.db.is_open:
            bd_anterior = self.ruta_bd
            self.db.close()
            self.ruta_bd = None
            messagebox.showinfo(
                "Base de datos de Paciente cerrada",
                f"Se ha cerrado la base de datos de Paciente:\n{bd_anterior}"
            )
            
            # Limpiar vista y deshabilitar menús de edición
            if hasattr(self, "analisis_view"):
                self.analisis_view.clear()
            if hasattr(self, "charts_view"):
                self.charts_view.clear()

            self._actualizar_estado_menus()

        else:
            messagebox.showwarning(
                "Sin base de datos de Paciente",
                "No hay ninguna base de datos de Paciente abierta."
            )

    def cerrar_aplicacion(self):
        # Aquí podríamos hacer limpieza antes de salir
        self.destroy()

    # ===========================
    #   MÉTODOS DEL MENÚ EDICIÓN
    # ===========================
    def _asegurar_bd_abierta(self) -> bool:
        """
        Comprueba si hay una base de datos abierta.
        Muestra un aviso y devuelve False si no la hay.
        """
        if self.db is None or not self.db.is_open:
            messagebox.showwarning(
                "Base de datos no disponible",
                "No hay ninguna base de datos de Paciente abierta.\n\n"
                "Crea o abre una base de datos desde el menú 'Archivo'."
            )
            return False
        return True

    def importar_analisis(self):
        """
        Importa un análisis desde un PDF:
        - Extrae los datos de hematología.
        - Los convierte a JSON (en memoria).
        - Inserta/reemplaza en la BD según la fecha del análisis.
        """
        if not self._asegurar_bd_abierta():
            return

        ruta = filedialog.askopenfilename(
            title="Seleccionar informe de laboratorio (PDF)",
            filetypes=[
                ("Archivos PDF", "*.pdf"),
                ("Todos los archivos", "*.*")
            ]
        )
        if not ruta:
            return

        try:
            # 1) Parsear PDF -> dict con formato {"analisis": [ {...} ]}
            data = parse_hematology_pdf(ruta)

            # 2) Insertar / reemplazar en la BD
            ids = self.db.import_from_json(data)

            # 3) Refrescar la vista de análisis
            if hasattr(self, "analisis_view"):
                self.analisis_view.refresh()
            if hasattr(self, "charts_view"):
                self.charts_view.refresh()


            mensaje_ids = ", ".join(str(i) for i in ids) if ids else "(sin registros)"
            messagebox.showinfo(
                "Análisis importado",
                "Se ha importado el análisis desde el PDF.\n\n"
                f"Archivo: {ruta}\n"
                f"Registros afectados (ID): {mensaje_ids}"
            )
        except Exception as e:
            messagebox.showerror(
                "Error al importar desde PDF",
                f"No se ha podido importar el análisis desde:\n{ruta}\n\n"
                f"Detalle del error:\n{e}"
            )

    # =============================
    #   MÉTODOS DEL MENÚ CONFIGURACION
    # =============================
    def configurar_rangos(self):
        """
        Abre el diálogo de configuración de rangos.
        Al cerrar, refresca AnalisisView y ChartsView para que
        usen los rangos actualizados.
        """
        # Por si acaso
        if not hasattr(self, "ranges_manager") or self.ranges_manager is None:
            self.ranges_manager = RangesManager()

        dialog = RangesDialog(self, self.ranges_manager)
        self.wait_window(dialog)

        if hasattr(self, "analisis_view"):
            self.analisis_view.set_ranges_manager(self.ranges_manager)
            self.analisis_view.refresh()

        if hasattr(self, "charts_view"):
            self.charts_view.set_ranges_manager(self.ranges_manager)
            self.charts_view.refresh()



    # ============================
    #   MÉTODO DEL MENÚ ACERCA DE
    # ============================
    def mostrar_acerca_de(self):
        mensaje = (
            "Aplicación de análisis de hematología\n\n"
            "Creado por: Borja Alonso Tristán\n"
            "Año: 2025"
        )
        messagebox.showinfo("Acerca de", mensaje)

    # ============================
    #   MÉTODOS AUXILIARES
    # ============================
    def _actualizar_estado_menus(self):
        """
        Habilita o deshabilita las opciones de Edición según si hay BD abierta.
        """
        if not hasattr(self, "menu_edicion"):
            return

        estado = "normal" if (self.db is not None and self.db.is_open) else "disabled"

        for label in [
            "Importar análisis desde PDF..."
        ]:
            try:
                self.menu_edicion.entryconfig(label, state=estado)
            except Exception:
                pass


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
