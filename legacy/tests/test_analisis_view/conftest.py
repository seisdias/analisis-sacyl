# tests/test_analisis_view/conftest.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


class FakeSheet:
    """
    Fake minimal para tksheet.Sheet: captura llamadas y argumentos.
    """

    def __init__(self):
        self._data = None
        self._headers = None
        self._col_widths: Dict[int, int] = {}
        self.highlight_calls: List[Dict[str, Any]] = []
        self.redraw_called = 0

    def set_sheet_data(self, data=None, **kwargs):
        self._data = data

    def headers(self, headers=None):
        self._headers = headers

    def column_width(self, idx: int, width: int):
        self._col_widths[idx] = width

    def highlight_cells(self, **kwargs):
        # tksheet acepta highlight_cells(cells="all", bg=None, fg=None,...)
        self.highlight_calls.append(kwargs)

    def redraw(self):
        self.redraw_called += 1


@dataclass
class FakeDB:
    """
    Fake DB configurable por atributo.
    """
    is_open: bool = True
    hematologia: Optional[List[Dict[str, Any]]] = None
    bioquimica: Optional[List[Dict[str, Any]]] = None
    orina: Optional[List[Dict[str, Any]]] = None
    gasometria: Optional[List[Dict[str, Any]]] = None
    patient: Optional[Dict[str, Any]] = None

    def list_hematologia(self, limit: int = 1000):
        return list(self.hematologia or [])

    def list_analyses(self, limit: int = 1000):
        # fallback viejo
        return list(self.hematologia or [])

    def list_bioquimica(self, limit: int = 1000):
        return list(self.bioquimica or [])

    def list_orina(self, limit: int = 1000):
        return list(self.orina or [])

    def list_gasometria(self, limit: int = 1000):
        return list(self.gasometria or [])

    def get_patient(self):
        return dict(self.patient) if self.patient else None


class FakeLabel:
    def __init__(self):
        self.text = None

    def configure(self, **kwargs):
        # ttk.Label.configure(text="...")
        self.text = kwargs.get("text", self.text)
