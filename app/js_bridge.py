from __future__ import annotations

from typing import List
import webview
from typing import Optional


class JsBridge:
    """
    Bridge entre JavaScript y Python (pywebview).
    Solo aquí se permite usar diálogos nativos.
    """

    def pick_open_db(self) -> Optional[str]:
        """Diálogo nativo: elegir BD existente."""
        if not self._window:
            return None
        import webview
        paths = self._window.create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=False,
            file_types=("SQLite DB (*.db;*.sqlite;*.sqlite3)", "*.db;*.sqlite;*.sqlite3"),
        )
        if not paths:
            return None
        return paths[0]

    def pick_new_db(self) -> Optional[str]:
        """Diálogo nativo: elegir ruta destino para crear BD nueva."""
        if not self._window:
            return None
        import webview
        paths = self._window.create_file_dialog(
            webview.SAVE_DIALOG,
            allow_multiple=False,
            save_filename="paciente.db",
            file_types=("SQLite DB (*.db)", "*.db"),
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

