from charts.series_provider import parse_date_yyyy_mm_dd, parse_float, DbSeriesProvider


class FakeDb:
    is_open = True

    def list_hematologia(self, limit=1000):
        return [
            {"fecha_analisis": "2025-11-11", "leucocitos": "0,4"},
            {"fecha_analisis": "bad-date", "leucocitos": "1,0"},
            {"fecha_analisis": "2025-11-12", "leucocitos": None},
            {"fecha_analisis": "2025-11-13", "leucocitos": 2},
        ]

    def list_bioquimica(self, limit=1000): return []
    def list_gasometria(self, limit=1000): return []
    def list_orina(self, limit=1000): return []


def test_parse_date_ok_and_bad():
    assert parse_date_yyyy_mm_dd("2025-11-11") is not None
    assert parse_date_yyyy_mm_dd("bad") is None
    assert parse_date_yyyy_mm_dd("") is None


def test_parse_float_ok_and_bad():
    assert parse_float("0,4") == 0.4
    assert parse_float("1.5") == 1.5
    assert parse_float(None) is None
    assert parse_float("bad") is None


def test_provider_returns_sorted_filtered_points():
    db = FakeDb()
    provider = DbSeriesProvider(db)
    points = provider.get_series("leucocitos")

    # Solo deben quedar 2 puntos válidos: 2025-11-11 (0.4) y 2025-11-13 (2.0)
    assert len(points) == 2
    assert points[0].value == 0.4
    assert points[1].value == 2.0
    assert points[0].date.strftime("%Y-%m-%d") == "2025-11-11"
    assert points[1].date.strftime("%Y-%m-%d") == "2025-11-13"
