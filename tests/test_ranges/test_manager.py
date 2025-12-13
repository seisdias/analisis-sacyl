import pytest

from ranges.manager import RangesManager
from ranges.defaults import DEFAULT_PARAM_RANGES

def test_reset_defaults_creates_deep_copy():
    m = RangesManager()
    some_key = next(iter(DEFAULT_PARAM_RANGES.keys()))

    # cambia en manager
    m.update_range(some_key, 1.0, 2.0)

    # defaults NO deben cambiar
    assert DEFAULT_PARAM_RANGES[some_key].min_value != 1.0 or DEFAULT_PARAM_RANGES[some_key].max_value != 2.0

def test_get_all_returns_dict_of_ranges():
    m = RangesManager()
    ranges = m.get_all()
    assert isinstance(ranges, dict)
    assert set(ranges.keys()) == set(DEFAULT_PARAM_RANGES.keys())

def test_update_range_unknown_key_raises_keyerror():
    m = RangesManager()
    with pytest.raises(KeyError):
        m.update_range("no_existe", 1.0, 2.0)

def test_get_by_category_groups_and_sorts_by_label():
    m = RangesManager()
    grouped = m.get_by_category()

    # todas las categorías deben existir como keys en grouped si hay elementos
    assert isinstance(grouped, dict)
    assert sum(len(v) for v in grouped.values()) == len(m.get_all())

    # comprobar orden por label dentro de cada categoría
    for cat, items in grouped.items():
        labels = [x.label for x in items]
        assert labels == sorted(labels)
