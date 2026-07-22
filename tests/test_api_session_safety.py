import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.routers import sessions as sessions_router
from api.server import app
from db import AnalysisDB


def _create_db(path: Path, marker: str | None = None) -> None:
    db = AnalysisDB(str(path))
    db.open()
    if marker is not None:
        db.conn.execute("CREATE TABLE original_marker(value TEXT)")
        db.conn.execute("INSERT INTO original_marker VALUES (?)", (marker,))
        db.conn.commit()
    db.close()


def test_session_upload_traversal_is_internal_and_same_names_do_not_collide(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source_one = tmp_path / "one.db"
    source_two = tmp_path / "two.db"
    _create_db(source_one, "one")
    _create_db(source_two, "two")
    client = TestClient(app)

    with source_one.open("rb") as first:
        response_one = client.post("/sessions/upload", files={"db_file": ("../same.db", first, "application/octet-stream")})
    with source_two.open("rb") as second:
        response_two = client.post("/sessions/upload", files={"db_file": ("../same.db", second, "application/octet-stream")})

    assert response_one.status_code == response_two.status_code == 200
    path_one = Path(response_one.json()["db_path"])
    path_two = Path(response_two.json()["db_path"])
    assert path_one.parent == path_two.parent == (tmp_path / "data/uploads").resolve()
    assert path_one != path_two
    assert not (tmp_path / "same.db").exists()
    with sqlite3.connect(path_one) as conn:
        assert conn.execute("SELECT value FROM original_marker").fetchone()[0] == "one"
    with sqlite3.connect(path_two) as conn:
        assert conn.execute("SELECT value FROM original_marker").fetchone()[0] == "two"


def test_session_upload_rejects_non_sqlite_and_cleans_it(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    response = TestClient(app).post(
        "/sessions/upload",
        files={"db_file": ("fake.db", b"not sqlite", "application/octet-stream")},
    )
    assert response.status_code == 400
    assert list((tmp_path / "data/uploads").iterdir()) == []


def test_session_upload_registration_failure_leaves_no_orphan(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "source.db"
    _create_db(source)
    monkeypatch.setattr(
        sessions_router.sessions,
        "open_existing",
        lambda _path: (_ for _ in ()).throw(RuntimeError("registration failed")),
    )

    with source.open("rb") as uploaded:
        response = TestClient(app).post(
            "/sessions/upload",
            files={"db_file": ("source.db", uploaded, "application/octet-stream")},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "No se pudo cargar la BD"
    assert list((tmp_path / "data/uploads").iterdir()) == []


@pytest.mark.parametrize("kind", ["directory", "non_sqlite", "bad_extension"])
def test_session_open_rejects_invalid_targets(tmp_path, kind):
    if kind == "directory":
        target = tmp_path / "folder.db"
        target.mkdir()
    elif kind == "non_sqlite":
        target = tmp_path / "fake.db"
        target.write_bytes(b"not sqlite")
    else:
        target = tmp_path / "valid.txt"
        _create_db(target)

    response = TestClient(app).post("/sessions/open", json={"db_path": str(target)})
    assert response.status_code == 400


def test_session_open_rejects_missing_file(tmp_path):
    response = TestClient(app).post(
        "/sessions/open", json={"db_path": str(tmp_path / "missing.db")}
    )
    assert response.status_code == 404


def test_session_new_conflict_preserves_existing_database(tmp_path):
    target = tmp_path / "existing.db"
    _create_db(target, "keep")
    response = TestClient(app).post(
        "/sessions/new", json={"db_path": str(target), "overwrite": False}
    )
    assert response.status_code == 409
    with sqlite3.connect(target) as conn:
        assert conn.execute("SELECT value FROM original_marker").fetchone()[0] == "keep"


def test_session_new_failed_overwrite_preserves_original_and_cleans_temp(tmp_path, monkeypatch):
    target = tmp_path / "existing.db"
    _create_db(target, "keep")
    original_bytes = target.read_bytes()

    class FailingDB:
        def __init__(self, _path):
            pass

        def open(self):
            raise RuntimeError("schema failure")

        def close(self):
            pass

    monkeypatch.setattr(sessions_router, "AnalysisDB", FailingDB)
    response = TestClient(app).post(
        "/sessions/new", json={"db_path": str(target), "overwrite": True}
    )

    assert response.status_code == 400
    assert target.read_bytes() == original_bytes
    assert sorted(tmp_path.iterdir()) == [target]


def test_session_new_successful_overwrite_replaces_initialized_database(tmp_path):
    target = tmp_path / "existing.db"
    _create_db(target, "replace")
    response = TestClient(app).post(
        "/sessions/new", json={"db_path": str(target), "overwrite": True}
    )

    assert response.status_code == 200
    with sqlite3.connect(target) as conn:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "analisis" in tables
    assert "original_marker" not in tables
    assert sorted(tmp_path.iterdir()) == [target]


def test_session_new_closes_database_before_atomic_replace(tmp_path, monkeypatch):
    target = tmp_path / "new.db"
    real_db = sessions_router.AnalysisDB
    real_replace = sessions_router.os.replace
    instances = []

    class TrackingDB(real_db):
        def __init__(self, path):
            super().__init__(path)
            self.closed_before_replace = False
            instances.append(self)

        def close(self):
            super().close()
            self.closed_before_replace = self.conn is None and not self.is_open

    def checked_replace(source, destination):
        assert instances[-1].closed_before_replace
        assert instances[-1].conn is None
        real_replace(source, destination)

    monkeypatch.setattr(sessions_router, "AnalysisDB", TrackingDB)
    monkeypatch.setattr(sessions_router.os, "replace", checked_replace)

    response = TestClient(app).post("/sessions/new", json={"db_path": str(target)})

    assert response.status_code == 200
    assert target.is_file()
