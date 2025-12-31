# tests/test_analisis_view/test_view.py
from __future__ import annotations

from tests.test_analisis_view.conftest import FakeDB, FakeLabel


class FakeTab:
    def __init__(self):
        self.db_set = None
        self.refresh_called = 0
        self.clear_called = 0

    def set_db(self, db):
        self.db_set = db

    def refresh(self, *args, **kwargs):
        self.refresh_called += 1

    def clear(self):
        self.clear_called += 1

    def set_ranges_manager(self, rm):
        self.rm_set = rm


def test_view_sets_patient_info_and_refresh_calls_tabs():
    from analisis_view.view import AnalisisView

    db = FakeDB(
        patient={
            "nombre": "Borja",
            "apellidos": "Alonso",
            "numero_historia": "NHC-1",
            "fecha_nacimiento": "1980-01-01",
            "sexo": "M",
        }
    )

    view = AnalisisView.__new__(AnalisisView)
    view.db = db
    view.ranges_manager = None

    # labels fake
    view.meta_labels = {
        "paciente": FakeLabel(),
        "nhc": FakeLabel(),
        "fnac": FakeLabel(),
        "sexo": FakeLabel(),
    }

    # tabs fake
    view.tab_hema = FakeTab()
    view.tab_bioq = FakeTab()
    view.tab_gaso = FakeTab()
    view.tab_orina = FakeTab()

    # Ejecutar update paciente y refresh
    view._update_patient_info()
    assert "Borja Alonso" in view.meta_labels["paciente"].text
    assert "NHC-1" in view.meta_labels["nhc"].text

    view.refresh()
    assert view.tab_hema.refresh_called == 1
    assert view.tab_bioq.refresh_called == 1
    assert view.tab_gaso.refresh_called == 1
    assert view.tab_orina.refresh_called == 1


def test_view_clear_resets_patient_info_and_clears_tabs():
    from analisis_view.view import AnalisisView

    db = FakeDB(patient={"nombre": "X"})
    view = AnalisisView.__new__(AnalisisView)
    view.db = db
    view.ranges_manager = None
    view.meta_labels = {
        "paciente": FakeLabel(),
        "nhc": FakeLabel(),
        "fnac": FakeLabel(),
        "sexo": FakeLabel(),
    }
    view.tab_hema = FakeTab()
    view.tab_bioq = FakeTab()
    view.tab_gaso = FakeTab()
    view.tab_orina = FakeTab()

    view.clear()
    assert view.tab_hema.clear_called == 1
    assert view.tab_bioq.clear_called == 1
    assert view.tab_gaso.clear_called == 1
    assert view.tab_orina.clear_called == 1
    assert "Paciente: -" in view.meta_labels["paciente"].text
