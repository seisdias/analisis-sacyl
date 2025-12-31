from charts.controller import ChartsController


class FakeRanges:
    def get_all(self):
        class PR:
            min_value = 0.0
            max_value = 10.0
        return {"leucocitos": PR()}


class FakeDb:
    is_open = True

    def list_hematologia(self, limit=1000):
        return [{"fecha_analisis": "2025-11-11", "leucocitos": "0,4"}]

    def list_bioquimica(self, limit=1000): return []
    def list_gasometria(self, limit=1000): return []
    def list_orina(self, limit=1000): return []


def test_controller_builds_figures_only_when_ready():
    c = ChartsController(db=None)
    assert c.build_figures(["leucocitos"]) == []

    c.set_db(FakeDb())
    figs = c.build_figures(["leucocitos"])
    assert len(figs) == 1
    param_name, fig = figs[0]
    assert param_name == "leucocitos"
    assert fig is not None
