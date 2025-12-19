# app/web_main.py
# -*- coding: utf-8 -*-
from __future__ import annotations

import threading
import time
import webbrowser
from dataclasses import dataclass
from typing import Optional

import uvicorn

from api.server import app


@dataclass
class _ServerHandle:
    server: uvicorn.Server
    thread: threading.Thread
    base_url: str


def _start_server(host: str = "127.0.0.1", port: int = 8000) -> _ServerHandle:
    config = uvicorn.Config(app, host=host, port=port, log_level="info", reload=False)
    server = uvicorn.Server(config)

    def run():
        server.run()

    t = threading.Thread(target=run, daemon=True)
    t.start()

    # Pequeña espera para que el server levante
    time.sleep(0.25)
    return _ServerHandle(server=server, thread=t, base_url=f"http://{host}:{port}")


class JsBridge:
    """API expuesta a JS cuando se ejecuta dentro de pywebview."""

    def __init__(self) -> None:
        self._window = None  # se asigna tras create_window

    def attach_window(self, window) -> None:
        self._window = window

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


def main() -> None:
    srv = _start_server(host="127.0.0.1", port=8000)
    shell_url = f"{srv.base_url}/web/shell.html?base={srv.base_url}"

    try:
        import webview

        bridge = JsBridge()
        win = webview.create_window(
            "salud_v1 (UI moderna)",
            shell_url,
            width=1300,
            height=900,
            js_api=bridge,
        )
        bridge.attach_window(win)

        # Cuando cierres la ventana, paramos el server
        def on_closed():
            try:
                srv.server.should_exit = True
            except Exception:
                pass

        win.events.closed += on_closed

        webview.start()
    except ModuleNotFoundError:
        # Fallback a navegador (modo web)
        webbrowser.open(shell_url)

        # En modo navegador, dejamos el server en primer plano
        # (si cierras el navegador, el server sigue: CTRL+C para parar)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            srv.server.should_exit = True


if __name__ == "__main__":
    main()
