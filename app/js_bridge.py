from __future__ import annotations

from importlib import import_module
from typing import Any, Optional


class JsBridge:
    """
    Bridge entre JavaScript y Python (pywebview).
    Solo aquí se permite usar diálogos nativos.
    """

    def __init__(self, webview_module: Any | None = None):
        self._webview_module = webview_module

    def _webview(self):
        if self._webview_module is not None:
            return self._webview_module
        try:
            return import_module("webview")
        except (ImportError, ModuleNotFoundError):
            return None

    def _get_window(self):
        webview = self._webview()
        windows = getattr(webview, "windows", None) if webview else None
        return windows[0] if windows else None

    def _pick(self, dialog_name: str, **kwargs):
        webview = self._webview()
        window = self._get_window()
        if webview is None or window is None:
            return None
        try:
            return window.create_file_dialog(getattr(webview, dialog_name), **kwargs)
        except Exception:
            return None

    def pick_open_db(self) -> Optional[str]:
        """Diálogo nativo: elegir BD existente."""
        paths = self._pick(
            "OPEN_DIALOG",
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
        paths = self._pick(
            "SAVE_DIALOG",
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
        paths = self._pick(
            "OPEN_DIALOG",
            allow_multiple=True,
            file_types=("PDF (*.pdf)", "*.pdf"),
        )
        return list(paths or [])
