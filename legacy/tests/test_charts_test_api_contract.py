from charts.factory import DefaultChartsFactory


def test_factory_creates_charts_view():
    # No creamos Tk root real aquí para evitar GUI;
    # solo comprobamos que la factory existe y tiene método create.
    factory = DefaultChartsFactory()
    assert hasattr(factory, "create")
    # El resto lo validaremos en tests Tk (Paso 3) con root oculto.
