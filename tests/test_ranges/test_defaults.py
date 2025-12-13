from ranges.defaults import DEFAULT_PARAM_RANGES
from ranges.models import ParamRange

def test_defaults_is_non_empty():
    assert isinstance(DEFAULT_PARAM_RANGES, dict)
    assert len(DEFAULT_PARAM_RANGES) > 0

def test_defaults_values_are_paramrange_and_keys_match():
    for k, v in DEFAULT_PARAM_RANGES.items():
        assert isinstance(v, ParamRange)
        assert v.key == k
