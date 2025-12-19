# webcharts/launcher.py
import threading
import socket
import time
from typing import Optional

import uvicorn

from api.server import app, set_db_path


def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class WebChartsLauncher:
    def __init__(self, db_path):
        self.db_path = db_path
        self.port: Optional[int] = None
        self._server: Optional[uvicorn.Server] = None
        self._thread: Optional[threading.Thread] = None

    def start_api(self) -> str:
        set_db_path(self.db_path)
        self.port = _free_port()

        config = uvicorn.Config(app, host="127.0.0.1", port=self.port, log_level="warning")
        self._server = uvicorn.Server(config)

        def run():
            self._server.run()

        self._thread = threading.Thread(target=run, daemon=True)
        self._thread.start()
        time.sleep(0.25)  # “smoke test” simple
        return f"http://127.0.0.1:{self.port}"

    def open_window(self, url: str) -> None:
        try:
            import webview
            webview.create_window("Gráficas (nuevo)", url, width=1200, height=800)
            webview.start()
        except ModuleNotFoundError:
            import webbrowser
            webbrowser.open(url)

    def stop_api(self) -> None:
        if self._server:
            self._server.should_exit = True

    def open_dashboard(self, base_url: str) -> None:
        self.open_window(f"{base_url}/web/dashboard.html?base={base_url}")
