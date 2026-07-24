import os
import sys
from copy import deepcopy
from pathlib import Path

import pytest

# Asegura que el root del repo está en sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from api.deps import sessions
from api.routers import charts as charts_router
from api.server import app

# Backend headless para matplotlib
os.environ.setdefault("MPLBACKEND", "Agg")


@pytest.fixture
def isolated_api(tmp_path, monkeypatch):
    """Isolate process-global API state and all filesystem writes."""
    with sessions._lock:
        previous_sessions = dict(sessions._sessions)
    had_legacy_path = hasattr(app.state, "db_path")
    previous_legacy_path = getattr(app.state, "db_path", None)
    previous_ranges = deepcopy(charts_router._RM.get_all())
    previous_overrides = dict(app.dependency_overrides)

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SALUD_V1_DATA_DIR", str(tmp_path / "salud-data"))
    if hasattr(app.state, "db_path"):
        delattr(app.state, "db_path")

    with TestClient(app) as client:
        try:
            yield client
        finally:
            with sessions._lock:
                sessions._sessions.clear()
                sessions._sessions.update(previous_sessions)
            app.dependency_overrides.clear()
            app.dependency_overrides.update(previous_overrides)
            charts_router._RM._ranges = previous_ranges
            if had_legacy_path:
                app.state.db_path = previous_legacy_path
            elif hasattr(app.state, "db_path"):
                delattr(app.state, "db_path")
