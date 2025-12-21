from __future__ import annotations

from typing import List
import webview
from typing import Optional


class JsBridge:
    """
    Bridge entre JavaScript y Python (pywebview).
    Solo aquí se permite usar diálogos nativos.
    """

    def _get_window(self):
        # webview.windows existe cuando la ventana ya está creada
        return webview.windows[0] if webview.windows else None

    def pick_open_db(self) -> Optional[str]:
        """Diálogo nativo: elegir BD existente."""
        w = self._get_window()
        if not w:
            return None

        paths = w.create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=False,
            file_types=(
                "SQLite DB (*.db;*.sqlite;*.sqlite3)",
                "All files (*.*)",
            ),
        )
        if not paths:
            return None
        return paths[0]

    def pick_new_db(self) -> Optional[str]:
        """Diálogo nativo: elegir ruta destino para crear BD nueva."""
        w = self._get_window()
        if not w:
            return None

        paths = w.create_file_dialog(
            webview.SAVE_DIALOG,
            allow_multiple=False,
            save_filename="paciente.db",
            file_types=(
                "SQLite DB (*.db;*.sqlite;*.sqlite3)",
                "All files (*.*)",
            ),
        )
        if not paths:
            return None
        return paths[0]


    def pick_import_pdfs(self) -> list[str]:
        """
        Abre un selector nativo de archivos PDF.
        Devuelve una lista de rutas absolutas.
        """
        paths = webview.windows[0].create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=True,
            file_types=("PDF (*.pdf)", "*.pdf"),
        )
        return list(paths or [])

