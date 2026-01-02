from charts.proxy_histograms import rbc_size_distribution_proxy

def test_rbc_proxy_ok():
    out = rbc_size_distribution_proxy(vcm=90.0, rdw=13.0)
    assert out["ok"] is True
    assert len(out["x"]) == len(out["y"]) and len(out["x"]) > 10
    assert abs(max(out["y"]) - 1.0) < 1e-9
    assert any(m["name"] == "VCM" for m in out["markers"])

def test_rbc_proxy_missing_vcm():
    out = rbc_size_distribution_proxy(vcm=None, rdw=13.0)
    assert out["ok"] is False
    assert out["x"] == []
