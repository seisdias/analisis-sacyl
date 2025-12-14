import pytest
tk = pytest.importorskip("tkinter")

from ranges.manager import RangesManager
from ranges.dialog import RangesDialog

def test_dialog_can_be_created_and_destroyed():
    root = tk.Tk()
    root.withdraw()
    try:
        dlg = RangesDialog(root, RangesManager())
        dlg.update_idletasks()
        dlg.destroy()
    finally:
        root.destroy()
