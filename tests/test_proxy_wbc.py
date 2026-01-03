from charts.proxy_histograms import wbc_differential_proxy

def test_wbc_proxy_ok_pct():
    out = wbc_differential_proxy(
        neutro_pct=60, linf_pct=30, mono_pct=7, eos_pct=2, baso_pct=1,
        neutro_abs=None, linf_abs=None, mono_abs=None, eos_abs=None, baso_abs=None,
    )
    assert out["ok"] is True
    assert out["categories"][0] == "Neutrófilos"
    assert abs(sum(out["pct"]) - 100) < 1e-6

def test_wbc_proxy_missing_all():
    out = wbc_differential_proxy(
        neutro_pct=None, linf_pct=None, mono_pct=None, eos_pct=None, baso_pct=None,
        neutro_abs=None, linf_abs=None, mono_abs=None, eos_abs=None, baso_abs=None,
    )
    assert out["ok"] is False
