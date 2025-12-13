import tkinter as tk

import pytest

from charts.view_tk import TkChartsView


class FakeDb:
    is_open = True

    def list_hematologia(self, limit=1000):
        return [{"fecha_analisis": "2025-11-11", "leucocitos": "0,4"}]

    def list_bioquimica(self, limit=1000): return []
    def list_gasometria(self, limit=1000): return []
    def list_orina(self, limit=1000): return []


@pytest.fixture
def tk_root():
    root = tk.Tk()
    root.withdraw()  # Importantísimo: no ventana real
    yield root
    root.destroy()


def test_tk_charts_view_can_instantiate(tk_root):
    view = TkChartsView(tk_root, db=FakeDb())
    view.pack()
    # No explota y existe
    assert view.winfo_exists() == 1


def test_refresh_with_no_selection_clears(tk_root):
    view = TkChartsView(tk_root, db=FakeDb())
    view.pack()

    view.refresh()
    # si no hay parámetros seleccionados, no debe crear widgets de gráficas
    assert len(view._figure_canvases) == 0


def test_refresh_with_selection_renders_canvas(tk_root):
    view = TkChartsView(tk_root, db=FakeDb())
    view.pack()

    # Selecciona un parámetro existente
    assert "leucocitos" in view._param_vars
    view._param_vars["leucocitos"].set(True)

    view.refresh()

    assert len(view._figure_canvases) == 1
    # Debe existir al menos un widget hijo en charts_frame
    assert len(view._charts_frame.winfo_children()) >= 1


def test_clear_removes_widgets(tk_root):
    view = TkChartsView(tk_root, db=FakeDb())
    view.pack()

    view._param_vars["leucocitos"].set(True)
    view.refresh()
    assert len(view._figure_canvases) == 1

    view.clear()
    assert len(view._figure_canvases) == 0
    assert len(view._charts_frame.winfo_children()) == 0
