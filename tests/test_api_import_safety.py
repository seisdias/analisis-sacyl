from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from starlette.datastructures import UploadFile

from api.deps import sessions
from api.routers import imports as imports_router
from api.server import app
from db import AnalysisDB


def _parsed_data(request_number="REQ-1"):
    return {
        "paciente": {"nombre": "Nuevo", "numero_historia": "N-1"},
        "hematologia": [{
            "fecha_analisis": "2026-07-22",
            "numero_peticion": request_number,
            "origen": "TEST",
            "leucocitos": 5.0,
        }],
        "bioquimica": [{
            "fecha_analisis": "2026-07-22",
            "numero_peticion": request_number,
            "glucosa": 90.0,
        }],
        "gasometria": [{
            "fecha_analisis": "2026-07-22",
            "numero_peticion": request_number,
            "gaso_ph": 7.4,
        }],
        "orina": [{
            "fecha_analisis": "2026-07-22",
            "numero_peticion": request_number,
            "ph": 6.0,
        }],
    }


@pytest.fixture
def import_api(tmp_path, monkeypatch):
    upload_dir = tmp_path / "controlled-uploads"
    upload_dir.mkdir()
    db = AnalysisDB(str(tmp_path / "import.db"))
    db.open()
    db.close()
    info = sessions.register(str(tmp_path / "import.db"))
    monkeypatch.setattr(imports_router, "uploads_dir", lambda: upload_dir)
    monkeypatch.setattr(imports_router, "parse_hematology_pdf", lambda _path: _parsed_data())
    try:
        yield TestClient(app), info.session_id, upload_dir
    finally:
        sessions.close(info.session_id)


@pytest.mark.parametrize("filename", ["../escape.pdf", "/tmp/absolute.pdf"])
def test_pdf_upload_external_name_never_decides_destination(import_api, tmp_path, monkeypatch, filename):
    client, session_id, upload_dir = import_api
    parsed_paths = []
    monkeypatch.setattr(
        imports_router,
        "parse_hematology_pdf",
        lambda path: parsed_paths.append(Path(path)) or _parsed_data(Path(path).stem),
    )

    response = client.post(
        f"/imports/upload?session_id={session_id}",
        files={"pdf_files": (filename, b"%PDF-1.7\ncontent", "application/pdf")},
    )

    assert response.status_code == 200
    assert response.json()["imported"] == 1
    assert len(parsed_paths) == 1
    assert parsed_paths[0].parent == upload_dir
    assert parsed_paths[0].name not in {"escape.pdf", "absolute.pdf"}
    assert not (tmp_path / "escape.pdf").exists()
    assert list(upload_dir.iterdir()) == []


@pytest.mark.parametrize(
    ("filename", "content", "message"),
    [
        ("report.txt", b"%PDF-1.7\n", "Extensión no válida"),
        ("report.PDF", b"not a pdf", "contenido no es un PDF"),
    ],
)
def test_pdf_upload_rejects_invalid_extension_or_content(import_api, filename, content, message):
    client, session_id, upload_dir = import_api
    response = client.post(
        f"/imports/upload?session_id={session_id}",
        files={"pdf_files": (filename, content, "application/octet-stream")},
    )

    assert response.status_code == 200
    assert response.json()["imported"] == 0
    assert message in response.json()["errors"][0]
    assert list(upload_dir.iterdir()) == []


@pytest.mark.anyio
async def test_pdf_upload_rejects_empty_name_and_leaves_no_temporary(import_api):
    _client, session_id, upload_dir = import_api
    request = next(info for info in [sessions.get(session_id)] if info is not None)
    db = AnalysisDB(request.db_path)
    db.open()
    try:
        result = await imports_router.import_upload(
            [UploadFile(file=BytesIO(b"%PDF-1.7\n"), filename="")], db
        )
    finally:
        db.close()

    assert result.imported == 0
    assert "Falta el nombre" in result.errors[0]
    assert list(upload_dir.iterdir()) == []


def test_same_pdf_names_use_distinct_internal_files_and_are_cleaned(import_api, monkeypatch):
    client, session_id, upload_dir = import_api
    parsed_paths = []

    def parse(path):
        parsed_paths.append(Path(path))
        return _parsed_data("REQ-" + str(len(parsed_paths)))

    monkeypatch.setattr(imports_router, "parse_hematology_pdf", parse)
    response = client.post(
        f"/imports/upload?session_id={session_id}",
        files=[
            ("pdf_files", ("same.pdf", b"%PDF-1.7\none", "application/pdf")),
            ("pdf_files", ("same.pdf", b"%PDF-1.7\ntwo", "application/pdf")),
        ],
    )

    assert response.json()["imported"] == 2
    assert parsed_paths[0] != parsed_paths[1]
    assert list(upload_dir.iterdir()) == []


def test_pdf_temporary_is_cleaned_after_parser_error(import_api, monkeypatch):
    client, session_id, upload_dir = import_api
    monkeypatch.setattr(
        imports_router, "parse_hematology_pdf", lambda _path: (_ for _ in ()).throw(ValueError("parser"))
    )
    response = client.post(
        f"/imports/upload?session_id={session_id}",
        files={"pdf_files": ("report.pdf", b"%PDF-1.7\n", "application/pdf")},
    )
    assert response.json()["imported"] == 0
    assert list(upload_dir.iterdir()) == []


def test_pdf_unlink_failure_does_not_change_success_result(import_api, monkeypatch):
    client, session_id, upload_dir = import_api

    with monkeypatch.context() as cleanup_patch:
        cleanup_patch.setattr(
            Path, "unlink", lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("busy"))
        )
        response = client.post(
            f"/imports/upload?session_id={session_id}",
            files={"pdf_files": ("report.pdf", b"%PDF-1.7\n", "application/pdf")},
        )

    assert response.status_code == 200
    assert response.json()["imported"] == 1
    for leftover in upload_dir.iterdir():
        leftover.unlink()


def test_pdf_temporary_is_cleaned_after_sqlite_error_without_exposing_path(import_api, monkeypatch):
    client, session_id, upload_dir = import_api

    def fail_import(path, _db):
        raise RuntimeError(f"SQLite failure while reading {path}")

    monkeypatch.setattr(imports_router, "_import_pdf_into_db", fail_import)
    response = client.post(
        f"/imports/upload?session_id={session_id}",
        files={"pdf_files": ("report.pdf", b"%PDF-1.7\n", "application/pdf")},
    )

    assert response.json()["imported"] == 0
    assert str(upload_dir) not in response.json()["errors"][0]
    assert list(upload_dir.iterdir()) == []


def test_import_endpoints_share_frontend_counter_contract(import_api, monkeypatch, tmp_path):
    client, session_id, _upload_dir = import_api
    upload_response = client.post(
        f"/imports/upload?session_id={session_id}",
        files={"pdf_files": ("report.pdf", b"%PDF-1.7\n", "application/pdf")},
    )

    local_pdf = tmp_path / "selected.pdf"
    monkeypatch.setattr(imports_router, "parse_hematology_pdf", lambda _path: _parsed_data("REQ-PATH"))
    paths_response = client.post(
        f"/imports/from_paths?session_id={session_id}",
        json={"pdf_paths": [str(local_pdf)]},
    )

    assert set(upload_response.json()) == {"imported", "errors"}
    assert set(paths_response.json()) == {"imported", "errors"}
    assert upload_response.json()["imported"] == paths_response.json()["imported"] == 1
    frontend = (Path(__file__).resolve().parents[1] / "web/assets/app.js").read_text(encoding="utf-8")
    assert "j.imported" in frontend
    assert "j.ok" not in frontend


def test_from_paths_error_does_not_expose_absolute_source_path(import_api, monkeypatch, tmp_path):
    client, session_id, _upload_dir = import_api
    source = tmp_path / "private" / "report.pdf"
    monkeypatch.setattr(
        imports_router,
        "_import_pdf_into_db",
        lambda path, _db: (_ for _ in ()).throw(RuntimeError(f"failed at {path}")),
    )

    response = client.post(
        f"/imports/from_paths?session_id={session_id}", json={"pdf_paths": [str(source)]}
    )

    assert response.json()["imported"] == 0
    assert str(source) not in response.json()["errors"][0]
    assert response.json()["errors"][0].startswith("report.pdf:")


@pytest.mark.parametrize(
    ("component", "method"),
    [
        ("hematologia", "insert_hematologia"),
        ("bioquimica", "insert_bioquimica"),
        ("gasometria", "insert_gasometria"),
        ("orina", "insert_orina"),
    ],
)
def test_component_failure_rolls_back_entire_pdf(tmp_path, monkeypatch, component, method):
    db = AnalysisDB(str(tmp_path / "atomic.db"))
    db.open()
    db.save_patient({"nombre": "Original", "numero_historia": "OLD"})
    monkeypatch.setattr(imports_router, "parse_hematology_pdf", lambda _path: _parsed_data())
    monkeypatch.setattr(db, method, lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError(component)))

    with pytest.raises(RuntimeError, match=component):
        imports_router._import_pdf_into_db("unused.pdf", db)

    assert db.get_patient()["nombre"] == "Original"
    for table in ("analisis", "hematologia", "bioquimica", "gasometria", "orina"):
        assert db.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0
    db.close()


def test_missing_request_number_does_not_modify_database(tmp_path, monkeypatch):
    db = AnalysisDB(str(tmp_path / "missing-request.db"))
    db.open()
    db.save_patient({"nombre": "Original"})
    monkeypatch.setattr(imports_router, "parse_hematology_pdf", lambda _path: _parsed_data(None))

    with pytest.raises(ValueError, match="numero_peticion"):
        imports_router._import_pdf_into_db("unused.pdf", db)

    assert db.get_patient()["nombre"] == "Original"
    assert db.conn.execute("SELECT COUNT(*) FROM analisis").fetchone()[0] == 0
    db.close()


def test_empty_component_values_are_rejected_before_begin(tmp_path, monkeypatch):
    db = AnalysisDB(str(tmp_path / "empty-component.db"))
    db.open()
    data = {
        "paciente": {"nombre": "No debe guardarse"},
        "hematologia": [{
            "fecha_analisis": "2026-07-22",
            "numero_peticion": "REQ-EMPTY",
            "leucocitos": None,
            "observaciones": "   ",
            "extra": {},
        }],
    }
    monkeypatch.setattr(imports_router, "parse_hematology_pdf", lambda _path: data)

    with pytest.raises(ValueError, match="no contiene componentes"):
        imports_router._import_pdf_into_db("unused.pdf", db)

    assert db.get_patient() is None
    assert db.conn.execute("SELECT COUNT(*) FROM analisis").fetchone()[0] == 0
    db.close()


def test_empty_patient_does_not_replace_existing_patient(tmp_path, monkeypatch):
    db = AnalysisDB(str(tmp_path / "empty-patient.db"))
    db.open()
    db.save_patient({"nombre": "Original", "numero_historia": "OLD"})
    data = _parsed_data()
    data["paciente"] = {"nombre": " ", "numero_historia": None}
    monkeypatch.setattr(imports_router, "parse_hematology_pdf", lambda _path: data)

    imports_router._import_pdf_into_db("unused.pdf", db)

    assert db.get_patient()["nombre"] == "Original"
    db.close()


def test_rollback_failure_does_not_hide_original_import_error(tmp_path, monkeypatch):
    db = AnalysisDB(str(tmp_path / "rollback-error.db"))
    db.open()
    real_conn = db.conn

    class RollbackFailingConnection:
        def execute(self, *args, **kwargs):
            return real_conn.execute(*args, **kwargs)

        def commit(self):
            return real_conn.commit()

        def rollback(self):
            raise RuntimeError("rollback failure")

    db.conn = RollbackFailingConnection()
    monkeypatch.setattr(imports_router, "parse_hematology_pdf", lambda _path: _parsed_data())
    monkeypatch.setattr(
        db, "insert_hematologia", lambda *_args, **_kwargs: (_ for _ in ()).throw(ValueError("original failure"))
    )

    with pytest.raises(ValueError, match="original failure"):
        imports_router._import_pdf_into_db("unused.pdf", db)

    real_conn.rollback()
    db.conn = real_conn
    db.close()


def test_valid_import_and_reimport_keep_upsert_behavior(tmp_path, monkeypatch):
    db = AnalysisDB(str(tmp_path / "valid.db"))
    db.open()
    data = _parsed_data()
    monkeypatch.setattr(imports_router, "parse_hematology_pdf", lambda _path: data)
    imports_router._import_pdf_into_db("unused.pdf", db)

    data["hematologia"][0]["leucocitos"] = 8.5
    imports_router._import_pdf_into_db("unused.pdf", db)

    assert db.conn.execute("SELECT COUNT(*) FROM analisis").fetchone()[0] == 1
    assert db.conn.execute("SELECT COUNT(*) FROM hematologia").fetchone()[0] == 1
    assert db.list_hematologia()[0]["leucocitos"] == 8.5
    db.close()


def test_close_is_idempotent_after_partial_open_failure(tmp_path, monkeypatch):
    db = AnalysisDB(str(tmp_path / "partial-open.db"))
    monkeypatch.setattr(
        db, "_create_tables", lambda: (_ for _ in ()).throw(RuntimeError("open failure"))
    )

    with pytest.raises(RuntimeError, match="open failure"):
        db.open()

    assert db.conn is not None
    assert not db.is_open
    db.close()
    db.close()
    assert db.conn is None
    assert not db.is_open
