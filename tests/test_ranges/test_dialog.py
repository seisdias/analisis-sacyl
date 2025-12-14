import pytest
tk = pytest.importorskip("tkinter")

from ranges.manager import RangesManager
from ranges.dialog import RangesDialog

def test_dialog_can_be_created_and_destroyed():
    try:
        root = tk.Tk()
    except tk.TclError as e:
        pytest.skip(f"Tk no usable en este entorno: {e}")

    root.withdraw()
    try:
        dlg = RangesDialog(root, RangesManager())
        dlg.update_idletasks()
        dlg.destroy()
    finally:
        root.destroy()

