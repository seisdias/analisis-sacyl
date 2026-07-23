from types import SimpleNamespace

import pytest

from api import deps


def test_get_db_closes_instance_when_open_fails(tmp_path, monkeypatch):
    closed = []

    class FailingDB:
        def __init__(self, _path):
            pass

        def open(self):
            raise RuntimeError("open failed")

        def close(self):
            closed.append(True)

    monkeypatch.setattr(deps, "AnalysisDB", FailingDB)
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(
        db_path=str(tmp_path / "never-opened.db")
    )))
    dependency = deps.get_db(request, None)
    with pytest.raises(RuntimeError, match="open failed"):
        next(dependency)
    assert closed == [True]
