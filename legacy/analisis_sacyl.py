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
import warnings
from app.app import AnalisisSACYLApp

warnings.warn(
        "analisis_sacyl.py está deprecado. Usa `app.main.py`.",
        DeprecationWarning,
        stacklevel=2,
    )


# ---------------------------------------------------------------------
#   CONFIGURACIÓN BÁSICA
# ---------------------------------------------------------------------

APP_TITLE = "Gestor de análisis clínicos – Hematología / Bioquímica / Orina / Gasometría"
APP_DEFAULT_SIZE = "1200x800"

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    app = AnalisisSACYLApp()
    app.mainloop()
