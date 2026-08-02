from __future__ import annotations

import importlib
import socket
import sys
import threading

import pytest


def test_web_main_import_does_not_require_pywebview(monkeypatch):
    real_import = importlib.import_module

    def guarded_import(name, package=None):
        if name == "webview":
            raise AssertionError("webview must not be imported")
        return real_import(name, package)

    monkeypatch.setattr(importlib, "import_module", guarded_import)
    sys.modules.pop("app.web_main", None)
    module = importlib.import_module("app.web_main")
    assert module._LOOPBACK == "127.0.0.1"


def test_explicit_port_is_used_and_server_becomes_ready(monkeypatch):
    from app import web_main

    probe = socket.socket()
    probe.bind((web_main._LOOPBACK, 0))
    port = probe.getsockname()[1]
    probe.close()
    monkeypatch.setenv("ANALISIS_SACYL_PORT", str(port))
    handle = web_main._start_server()
    try:
        assert handle.port == port
        assert web_main._request_status(handle.port, "/health") == 200
        assert handle.thread.is_alive()
    finally:
        handle.stop()
    assert not handle.thread.is_alive()


def test_occupied_port_fails_without_starting_thread():
    from app import web_main

    occupied = socket.socket()
    occupied.bind((web_main._LOOPBACK, 0))
    occupied.listen()
    try:
        with pytest.raises(OSError):
            web_main._start_server(port=occupied.getsockname()[1])
    finally:
        occupied.close()
    assert not any(t.name.startswith("analisis-sacyl-uvicorn-") for t in threading.enumerate())


def test_dynamic_port_readiness_shutdown_and_join():
    from app import web_main

    handle = web_main._start_server(port=0)
    assert handle.port > 0
    assert web_main._request_status(handle.port, "/web/shell.html") == 200
    handle.stop()
    assert not handle.thread.is_alive()
    with pytest.raises(OSError):
        socket.create_connection((web_main._LOOPBACK, handle.port), timeout=0.2)


def test_smoke_test_does_not_import_webview(monkeypatch, tmp_path):
    from app import web_main

    monkeypatch.setenv("ANALISIS_SACYL_DATA_DIR", str(tmp_path / "runtime"))
    monkeypatch.delitem(sys.modules, "webview", raising=False)
    monkeypatch.setattr(web_main, "import_module", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("webview imported")))
    assert web_main.main(["--smoke-test"]) == 0
    assert not (tmp_path / "runtime").exists()
    assert not any(t.name.startswith("analisis-sacyl-uvicorn-") for t in threading.enumerate())


@pytest.mark.parametrize("value", ["abc", "0", "65536"])
def test_invalid_configured_port_is_rejected(monkeypatch, value):
    from app import web_main

    monkeypatch.setenv("ANALISIS_SACYL_PORT", value)
    with pytest.raises(ValueError):
        web_main._start_server()
