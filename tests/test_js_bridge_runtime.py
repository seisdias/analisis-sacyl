from types import SimpleNamespace

from app.js_bridge import JsBridge


class DialogWindow:
    def __init__(self, result=None, error=None):
        self.result, self.error = result, error

    def create_file_dialog(self, *_args, **_kwargs):
        if self.error:
            raise self.error
        return self.result


def _webview(window=None):
    return SimpleNamespace(windows=[] if window is None else [window], OPEN_DIALOG="open", SAVE_DIALOG="save")


def test_bridge_handles_absent_window():
    bridge = JsBridge(_webview())
    assert bridge.pick_open_db() is None
    assert bridge.pick_new_db() is None
    assert bridge.pick_import_pdfs() == []


def test_bridge_handles_cancel_and_empty_list():
    assert JsBridge(_webview(DialogWindow(None))).pick_open_db() is None
    assert JsBridge(_webview(DialogWindow([]))).pick_new_db() is None
    assert JsBridge(_webview(DialogWindow([]))).pick_import_pdfs() == []


def test_bridge_handles_dialog_error():
    bridge = JsBridge(_webview(DialogWindow(error=RuntimeError("dialog failed"))))
    assert bridge.pick_open_db() is None
    assert bridge.pick_new_db() is None
    assert bridge.pick_import_pdfs() == []


def test_bridge_returns_selected_values():
    bridge = JsBridge(_webview(DialogWindow(["/tmp/uno.db", "/tmp/dos.db"])))
    assert bridge.pick_open_db() == "/tmp/uno.db"
    assert bridge.pick_import_pdfs() == ["/tmp/uno.db", "/tmp/dos.db"]
