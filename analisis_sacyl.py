# -*- coding: utf-8 -*-
"""
Aplicación principal de gestión de análisis de laboratorio SACYL.

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

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional, List

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from db_manager import HematologyDB
from analisis_view import AnalisisView
from charts_view import ChartsView
from ranges_config import RangesManager, RangesDialog
from lab_pdf import parse_hematology_pdf


# ---------------------------------------------------------------------
#   CONFIGURACIÓN BÁSICA
# ---------------------------------------------------------------------

APP_TITLE = "Gestor de análisis clínicos – Hematología / Bioquímica / Orina / Gasometría"
APP_DEFAULT_SIZE = "1200x800"

logger = logging.getLogger(__name__)


class AnalisisSACYLApp(tk.Tk):
    """
    Ventana principal de la aplicación de gestión de análisis.

    Responsabilidades:
      - Gestionar la BD (abrir / cerrar / crear).
      - Gestionar el menú principal.
      - Coordinar las vistas (AnalisisView y ChartsView).
      - Orquestar la importación de informes PDF.
    """

    def __init__(self) -> None:
        super().__init__()

        # Metadatos de la ventana
        self.title(APP_TITLE)
        self.geometry(APP_DEFAULT_SIZE)

        # Estado BD
        self.db: Optional[HematologyDB] = None
        self.db_path: Optional[Path] = None

        # Rangos de referencia
        self.ranges_manager = RangesManager()

        # Referencias a menús que necesitan enable/disable
        self.menu_archivo: Optional[tk.Menu] = None
        self.menu_edicion: Optional[tk.Menu] = None
        self.menu_config: Optional[tk.Menu] = None

        # Vistas
        self.notebook: ttk.Notebook
        self.tab_datos: ttk.Frame
        self.tab_graficas: ttk.Frame
        self.analisis_view: AnalisisView
        self.charts_view: ChartsView

        # Construcción interfaz
        self._build_menu()
        self._build_main_layout()

        # Gestión del cierre de ventana
        self.protocol("WM_DELETE_WINDOW", self._on_close_app)

    # -----------------------------------------------------------------
    #   MENÚ
    # -----------------------------------------------------------------
    def _build_menu(self) -> None:
        menubar = tk.Menu(self)

        # ---- Menú Archivo ----
        m_file = tk.Menu(menubar, tearoff=0)
        m_file.add_command(label="Nuevo paciente...", command=self.menu_new_db)
        m_file.add_command(label="Abrir datos paciente...", command=self.menu_open_db)
        m_file.add_separator()
        m_file.add_command(label="Cerrar datos", command=self.menu_close_db)
        m_file.add_separator()
        m_file.add_command(label="Cerrar aplicación", command=self._on_close_app)
        menubar.add_cascade(label="Archivo", menu=m_file)
        self.menu_archivo = m_file

        # ---- Menú Edición ----
        m_edit = tk.Menu(menubar, tearoff=0)
        m_edit.add_command(
            label="Importar análisis desde PDF...",
            command=self.menu_import_pdfs,
        )
        menubar.add_cascade(label="Edición", menu=m_edit)
        self.menu_edicion = m_edit

        # ---- Menú Configuración ----
        m_cfg = tk.Menu(menubar, tearoff=0)
        m_cfg.add_command(label="Rangos de parámetros...", command=self.menu_edit_ranges)
        menubar.add_cascade(label="Configuración", menu=m_cfg)
        self.menu_config = m_cfg

        self.config(menu=menubar)
        self._update_menus_state()

    # -----------------------------------------------------------------
    #   LAYOUT PRINCIPAL
    # -----------------------------------------------------------------
    def _build_main_layout(self) -> None:
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

    # -----------------------------------------------------------------
    #   UTILIDADES GENERALES
    # -----------------------------------------------------------------
    def _db_is_open(self) -> bool:
        return self.db is not None and getattr(self.db, "is_open", False)

    def _on_db_opened(self, path: Path) -> None:
        """
        Acciones comunes tras abrir/crear una base de datos.
        """
        self.db_path = path
        logger.info("Base de datos abierta: %s", path)

        # Enlazar BD con vistas
        self.refresh_all()
        self._update_menus_state()

    def _on_db_closed(self) -> None:
        """
        Acciones comunes tras cerrar una base de datos.
        """
        logger.info("Base de datos cerrada")
        self.db = None
        self.db_path = None

        # Desenlazar BD de las vistas
        self.analisis_view.set_db(None)
        self.charts_view.set_db(None)
        self.analisis_view.clear()
        self.charts_view.clear()

        self._update_menus_state()

    def _update_menus_state(self) -> None:
        """
        Activa/desactiva opciones según haya BD abierta o no.
        """
        state_db = "normal" if self._db_is_open() else "disabled"

        # Menú Edición: importar solo con BD abierta
        if self.menu_edicion is not None:
            try:
                self.menu_edicion.entryconfig("Importar análisis desde PDF...", state=state_db)
            except Exception:
                logger.exception("Error actualizando estado del menú Edición")

        # Menú Archivo: "Cerrar datos" solo si hay BD
        if self.menu_archivo is not None:
            try:
                # buscamos por índice porque el label podría cambiar en futuras versiones
                # (aquí sabemos que "Cerrar datos" es la tercera entrada: 0,1,2,3,4)
                # Mejor buscar por nombre en un futuro si se complica el menú.
                self.menu_archivo.entryconfig(3, state=state_db)
            except Exception:
                # Si falla, no es crítico
                pass

    # -----------------------------------------------------------------
    #   MENÚ ARCHIVO: NUEVO / ABRIR / CERRAR
    # -----------------------------------------------------------------
    def menu_new_db(self) -> None:
        path_str = filedialog.asksaveasfilename(
            title="Crear nueva base de datos de paciente",
            defaultextension=".db",
            filetypes=[
                ("Bases de datos SQLite", "*.db *.sqlite *.sqlite3"),
                ("Todos los archivos", "*.*"),
            ],
        )
        if not path_str:
            return

        path = Path(path_str)

        if path.exists():
            resp = messagebox.askyesno(
                "Sobrescribir base de datos",
                f"El archivo '{path}' ya existe.\n\n"
                "¿Deseas reemplazarlo por una nueva base de datos vacía?",
            )
            if not resp:
                return
            try:
                path.unlink()
            except OSError as e:
                messagebox.showerror(
                    "Error al borrar",
                    f"No se pudo eliminar el archivo existente:\n{e}",
                )
                return

        try:
            self.db = HematologyDB(str(path))
            self.db.open()
        except Exception as e:
            logger.exception("Error creando nueva base de datos")
            messagebox.showerror(
                "Error al crear base de datos",
                f"No se pudo crear la base de datos:\n{e}",
            )
            self.db = None
            return

        messagebox.showinfo(
            "Base de datos creada",
            f"Se ha creado la base de datos:\n{path}",
        )

        self._on_db_opened(path)

    def menu_open_db(self) -> None:
        path_str = filedialog.askopenfilename(
            title="Abrir base de datos de paciente",
            filetypes=[
                ("Bases de datos SQLite", "*.db *.sqlite *.sqlite3"),
                ("Todos los archivos", "*.*"),
            ],
        )
        if not path_str:
            return

        path = Path(path_str)

        if not path.exists():
            messagebox.showerror(
                "Archivo no existente",
                f"El archivo '{path}' no existe.",
            )
            return

        try:
            self.db = HematologyDB(str(path))
            self.db.open()
            print("BIOQ keys:", self.db.list_bioquimica(limit=1)[0].keys())
            print("ORINA keys:", self.db.list_orina(limit=1)[0].keys())
            print("stop")
        except Exception as e:
            logger.exception("Error abriendo base de datos")
            messagebox.showerror(
                "Error al abrir base de datos",
                f"No se pudo abrir la base de datos:\n{e}",
            )
            self.db = None
            return

        messagebox.showinfo(
            "Base de datos abierta",
            f"Se ha abierto la base de datos:\n{path}",
        )

        self._on_db_opened(path)

    def menu_close_db(self) -> None:
        if self.db:
            try:
                self.db.close()
            except Exception:
                logger.exception("Error cerrando base de datos")

        self._on_db_closed()

        messagebox.showinfo(
            "Base de datos cerrada",
            "Se han cerrado los datos del paciente.",
        )

    # -----------------------------------------------------------------
    #   MENÚ EDICIÓN: IMPORTAR PDF(S)
    # -----------------------------------------------------------------
    def menu_import_pdfs(self) -> None:
        if not self._db_is_open():
            messagebox.showwarning(
                "Sin base de datos",
                "No hay base de datos abierta.\n\n"
                "Crea o abre una base de datos desde el menú 'Archivo'.",
            )
            return

        rutas = filedialog.askopenfilenames(
            title="Seleccionar informes de laboratorio (PDF)",
            filetypes=[("Archivos PDF", "*.pdf")],
        )
        if not rutas:
            return

        ok_count = 0
        errores: List[str] = []

        for ruta in rutas:
            pdf_path = Path(ruta)
            try:
                self._import_single_pdf(pdf_path)
                ok_count += 1
            except ValueError as e:
                # Errores esperados: informe no soportado (radiología, alta, microbiología, citometría, etc.)
                logger.warning("Informe no soportado: %s (%s)", pdf_path, e)
                errores.append(f"{pdf_path.name}: {e}")
            except Exception as e:
                # Errores inesperados del parser u otros
                logger.exception("Error importando PDF: %s", pdf_path)
                errores.append(f"{pdf_path.name}: Error inesperado: {e}")

        # Refrescamos vistas una sola vez al final
        self.refresh_all()

        # Mensajes al usuario
        if errores and ok_count > 0:
            messagebox.showwarning(
                "Importación parcial",
                "Se importaron algunos informes, pero hubo errores:\n\n"
                + "\n".join(errores),
            )
        elif errores and ok_count == 0:
            messagebox.showerror(
                "Error en la importación",
                "No se pudo importar ningún informe:\n\n"
                + "\n".join(errores),
            )
        else:
            messagebox.showinfo(
                "Importación completada",
                f"Se importaron correctamente {ok_count} informe(s) de laboratorio.",
            )

    def _import_single_pdf(self, pdf_path: Path) -> None:
        """
        Importa un único informe PDF en la BD abierta.

        Levanta excepción si algo falla (se gestiona a nivel superior).
        """
        if not self._db_is_open():
            raise RuntimeError("No hay base de datos abierta")

        logger.info("Importando PDF: %s", pdf_path)

        data = parse_hematology_pdf(str(pdf_path))

        # Paciente (si viene)
        paciente = data.get("paciente")
        if isinstance(paciente, dict):
            self.db.save_patient(paciente)

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

    # -----------------------------------------------------------------
    #   MENÚ CONFIGURACIÓN: RANGOS
    # -----------------------------------------------------------------
    def menu_edit_ranges(self) -> None:
        dlg = RangesDialog(self, self.ranges_manager)
        dlg.wait_window()
        # Al cerrar el diálogo, refrescamos vistas
        self.analisis_view.refresh()
        self.charts_view.refresh()

    # -----------------------------------------------------------------
    #   REFRESCAR TODAS LAS VISTAS
    # -----------------------------------------------------------------
    def refresh_all(self) -> None:
        if not self._db_is_open():
            return

        self.analisis_view.set_db(self.db)
        self.charts_view.set_db(self.db)

        self.analisis_view.refresh()
        self.charts_view.refresh()

    # -----------------------------------------------------------------
    #   CIERRE DE APLICACIÓN
    # -----------------------------------------------------------------
    def _on_close_app(self) -> None:
        """
        Cierra la aplicación asegurando el cierre de la BD.
        """
        # Si quieres pedir confirmación al usuario, este es el sitio:
        # if not messagebox.askyesno("Salir", "¿Seguro que deseas cerrar la aplicación?"):
        #     return

        try:
            if self.db:
                self.db.close()
        except Exception:
            logger.exception("Error cerrando BD al salir")

        self.destroy()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app = AnalisisSACYLApp()
    app.mainloop()
