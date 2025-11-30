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
from pathlib import Path
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
        self.menu_edicion = tk.Menu(menubar, tearoff=0)
        self.menu_edicion.add_command(
            label="Importar análisis desde PDF...",
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

        self.header_label = tk.Label(
            container,
            text="Análisis de Hematología",
            font=("Segoe UI", 10),
            justify="center"
        )
        self.header_label.pack(side="top", pady=10)

        # Paned vertical para separar tabla (arriba) y gráficas (abajo)
        paned = ttk.PanedWindow(
            container,
            orient="vertical"
        )
        try:
            paned.configure(sashwidth=8, sashrelief="raised")
        except tk.TclError:
            # Algunos Tk no soportan estas opciones
            pass

        paned.pack(fill="both", expand=True, padx=10, pady=10)

        top_frame = ttk.Frame(paned)
        bottom_frame = ttk.Frame(paned)

        paned.add(top_frame, weight=3)
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

        # Inicializar texto de cabecera (sin paciente todavía)
        self._update_patient_label()

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
            self._update_patient_label()

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
            self._update_patient_label()

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
            self._update_patient_label()

        else:
            messagebox.showwarning(
                "Sin base de datos de Paciente",
                "No hay ninguna base de datos de Paciente abierta."
            )

    def cerrar_aplicacion(self):
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
        Importa uno o varios informes PDF de laboratorio.

        A partir de Fase 2:
        - Se importan HEMATOLOGÍA, BIOQUÍMICA y ORINA (si vienen en el PDF).
        """
        if not self._asegurar_bd_abierta():
            return

        rutas = filedialog.askopenfilenames(
            title="Seleccionar informes de laboratorio (PDF)",
            filetypes=[("Archivos PDF", "*.pdf")]
        )
        if not rutas:
            return

        ids_importados = []
        errores = []

        for ruta in rutas:
            try:
                # Parsea TODO el informe (paciente + hematología + bioquímica + orina)
                data = parse_hematology_pdf(ruta)

                # Importación completa:
                # - paciente (internamente hace check_and_update_patient)
                # - hematologia
                # - bioquimica
                # - orina
                ids = self.db.import_from_json(data)
                ids_importados.extend(ids)

            except Exception as e:
                errores.append(f"{Path(ruta).name}: {e}")

        # REFRESCAR UNA VEZ AL FINAL
        if hasattr(self, "analisis_view"):
            self.analisis_view.refresh()
        if hasattr(self, "charts_view"):
            self.charts_view.refresh()

        # Actualizar cabecera con posible paciente nuevo/actualizado
        self._update_patient_label()

        # MOSTRAR RESULTADO
        if errores and ids_importados:
            messagebox.showwarning(
                "Importación parcial",
                "Se importaron algunos análisis, pero hubo errores:\n\n"
                + "\n".join(errores)
            )
        elif errores and not ids_importados:
            messagebox.showerror(
                "Error en la importación",
                "No se pudo importar ningún análisis:\n\n"
                + "\n".join(errores)
            )
        else:
            messagebox.showinfo(
                "Importación completada",
                f"Se importaron {len(ids_importados)} análisis de hematología "
                f"(y, si existían, sus datos de bioquímica/orina)."
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

    def _update_patient_label(self):
        """
        Actualiza la etiqueta superior con los datos del paciente, si existen,
        en DOS LÍNEAS:
          - Línea 1: Nombre + Apellidos
          - Línea 2: Sexo | Fecha nacimiento | Nº Historia
        """
        base = "Análisis de Hematología"

        if self.db is None or not self.db.is_open:
            self.header_label.config(text=base, font=("Segoe UI", 10))
            return

        pac = None
        try:
            pac = self.db.get_patient()
        except Exception:
            pac = None

        if not pac:
            self.header_label.config(
                text=f"{base}\n\nPaciente: (sin datos)",
                font=("Segoe UI", 10),
            )
            return

        nombre = (pac.get("nombre") or "").strip()
        apellidos = (pac.get("apellidos") or "").strip()
        sexo = (pac.get("sexo") or "").strip()
        fecha_nac = (pac.get("fecha_nacimiento") or "").strip()
        historia = (pac.get("numero_historia") or "").strip()

        linea1 = f"{nombre} {apellidos}".strip()
        if not linea1:
            linea1 = "(sin nombre)"

        partes2 = []
        if sexo:
            partes2.append(f"Sexo: {sexo}")
        if fecha_nac:
            partes2.append(f"Nac.: {fecha_nac}")
        if historia:
            partes2.append(f"Historia: {historia}")

        linea2 = " | ".join(partes2) if partes2 else "(datos incompletos)"

        texto = f"{base}\n\n{linea1}\n{linea2}"

        self.header_label.config(text=texto, font=("Segoe UI", 10))


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