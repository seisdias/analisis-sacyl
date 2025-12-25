# app/web_main.py
# -*- coding: utf-8 -*-
from __future__ import annotations

import threading
import time
import webbrowser
from dataclasses import dataclass
from app.js_bridge import JsBridge
import logging
logger = logging.getLogger(__name__)


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

        # Cuando cierres la ventana, paramos el server
        def on_window_closed():
            logger.info("Ventana cerrada -> apagando servidor")
            srv.server.should_exit = True

        win.events.closed += on_window_closed

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
