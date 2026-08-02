from __future__ import annotations

import argparse
import http.client
import logging
import os
import socket
import sys
import threading
import time
import webbrowser
from dataclasses import dataclass
from importlib import import_module
from typing import Any, Sequence

import uvicorn

from api.server import app
from app.js_bridge import JsBridge

logger = logging.getLogger(__name__)
_LOOPBACK = "127.0.0.1"
_READY_TIMEOUT = 10.0
_JOIN_TIMEOUT = 10.0


@dataclass
class _ServerHandle:
    server: uvicorn.Server
    thread: threading.Thread
    base_url: str
    port: int

    def stop(self, timeout: float = _JOIN_TIMEOUT) -> None:
        self.server.should_exit = True
        self.thread.join(timeout)
        if self.thread.is_alive():
            self.server.force_exit = True
            self.thread.join(timeout)
        if self.thread.is_alive():
            raise RuntimeError("El servidor local no se detuvo dentro del plazo")


def _configured_port() -> int:
    raw = os.getenv("ANALISIS_SACYL_PORT")
    if raw is None or not raw.strip():
        return 0
    try:
        port = int(raw)
    except ValueError as exc:
        raise ValueError("ANALISIS_SACYL_PORT debe ser un entero entre 1 y 65535") from exc
    if not 1 <= port <= 65535:
        raise ValueError("ANALISIS_SACYL_PORT debe estar entre 1 y 65535")
    return port


def _request_status(port: int, path: str, timeout: float = 0.5) -> int:
    connection = http.client.HTTPConnection(_LOOPBACK, port, timeout=timeout)
    try:
        connection.request("GET", path)
        response = connection.getresponse()
        response.read()
        return response.status
    finally:
        connection.close()


def _wait_ready(handle: _ServerHandle, timeout: float = _READY_TIMEOUT) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not handle.thread.is_alive():
            raise RuntimeError("El servidor local terminó antes de estar listo")
        try:
            if _request_status(handle.port, "/health") == 200:
                return
        except OSError:
            pass
        time.sleep(0.02)
    raise TimeoutError("El servidor local no alcanzó readiness")


def _start_server(port: int | None = None, timeout: float = _READY_TIMEOUT) -> _ServerHandle:
    selected_port = _configured_port() if port is None else port
    if not 0 <= selected_port <= 65535:
        raise ValueError("El puerto debe estar entre 0 y 65535")

    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind((_LOOPBACK, selected_port))
        listener.listen(128)
        actual_port = listener.getsockname()[1]
    except Exception:
        listener.close()
        raise

    config = uvicorn.Config(app, host=_LOOPBACK, port=actual_port, log_level="warning", reload=False)
    server = uvicorn.Server(config)
    thread = threading.Thread(
        target=server.run,
        kwargs={"sockets": [listener]},
        name=f"analisis-sacyl-uvicorn-{actual_port}",
        daemon=True,
    )
    handle = _ServerHandle(server, thread, f"http://{_LOOPBACK}:{actual_port}", actual_port)
    thread.start()
    try:
        _wait_ready(handle, timeout)
    except Exception:
        handle.stop()
        raise
    return handle


def _shell_url(server: _ServerHandle) -> str:
    return f"{server.base_url}/web/shell.html?base={server.base_url}"


def _load_webview() -> Any:
    try:
        return import_module("webview")
    except (ImportError, ModuleNotFoundError) as exc:
        raise RuntimeError(
            "El modo desktop requiere pywebview; instale requirements-webview.txt"
        ) from exc


def _run_desktop(server: _ServerHandle) -> None:
    webview = _load_webview()
    bridge = JsBridge(webview)
    window = webview.create_window(
        "salud_v1 (UI moderna)", _shell_url(server), width=1300, height=900, js_api=bridge
    )
    window.events.closed += lambda: setattr(server.server, "should_exit", True)
    webview.start()


def _run_browser(server: _ServerHandle, *, open_browser: bool = True) -> None:
    if open_browser:
        webbrowser.open(_shell_url(server))
    try:
        while server.thread.is_alive():
            server.thread.join(0.5)
    except KeyboardInterrupt:
        pass


def _run_smoke_test() -> None:
    server = _start_server()
    try:
        if _request_status(server.port, "/health") != 200:
            raise RuntimeError("/health no respondió 200")
        if _request_status(server.port, "/web/shell.html") != 200:
            raise RuntimeError("/web/shell.html no respondió 200")
    finally:
        server.stop()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inicia la aplicación análisis SACYL")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--browser", action="store_true", help="usa el navegador del sistema")
    modes.add_argument("--desktop", action="store_true", help="usa una ventana pywebview")
    modes.add_argument("--smoke-test", action="store_true", help="valida backend y shell sin GUI")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.smoke_test:
        _run_smoke_test()
        return 0

    server = _start_server()
    try:
        if args.browser:
            _run_browser(server, open_browser="PYTEST_CURRENT_TEST" not in os.environ)
        elif args.desktop:
            _run_desktop(server)
        else:
            # Default explícito: conserva desktop con fallback a navegador.
            try:
                _run_desktop(server)
            except RuntimeError:
                _run_browser(server, open_browser="PYTEST_CURRENT_TEST" not in os.environ)
        return 0
    finally:
        server.stop()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, TimeoutError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
