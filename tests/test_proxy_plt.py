from charts.proxy_histograms import plt_size_distribution_proxy

def test_plt_proxy_ok():
    out = plt_size_distribution_proxy(vpm=10.0, plaquetas=200.0)
    assert out["ok"] is True
    assert len(out["x"]) == len(out["y"]) and len(out["x"]) > 10
    assert abs(max(out["y"]) - 1.0) < 1e-9
    assert any(m.get("name") == "VPM" for m in out["markers"])

def test_plt_proxy_missing_vpm():
    out = plt_size_distribution_proxy(vpm=None, plaquetas=200.0)
    assert out["ok"] is False
    assert out["x"] == []
