from ranges.models import ParamRange

def test_paramrange_dataclass_fields_roundtrip():
    pr = ParamRange(
        key="hb",
        label="Hemoglobina",
        category="Hematología",
        unit="g/dL",
        min_value=12.0,
        max_value=16.0,
    )
    assert pr.key == "hb"
    assert pr.label == "Hemoglobina"
    assert pr.category == "Hematología"
    assert pr.unit == "g/dL"
    assert pr.min_value == 12.0
    assert pr.max_value == 16.0
