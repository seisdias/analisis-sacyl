from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fastapi.testclient import TestClient

from api.deps import sessions
from api.server import app
from tests.api_helpers import create_versioned_db, session_query


def _open(client, path: Path) -> str:
    response = client.post("/sessions/open", json={"db_path": str(path)})
    assert response.status_code == 200, response.text
    return response.json()["session_id"]


def test_new_session_meta_patient_close_cycle(isolated_api, tmp_path):
    target = tmp_path / "new.db"
    created = isolated_api.post("/sessions/new", json={"db_path": str(target)})
    assert created.status_code == 200
    sid = created.json()["session_id"]

    meta = isolated_api.get("/meta")
    assert meta.status_code == 200
    assert {"defs", "groups"} <= set(meta.json())
    assert "leucocitos" in meta.json()["defs"]

    patient = isolated_api.get(f"/patient?{session_query(sid)}")
    assert patient.status_code == 200
    assert patient.json() == {"display_name": ""}

    closed = isolated_api.delete(f"/sessions/{sid}")
    assert closed.status_code == 200
    assert closed.json() == {"ok": True}
    assert isolated_api.get(f"/patient?{session_query(sid)}").status_code == 404


def test_open_versioned_database_reads_patient_and_series(
    isolated_api, tmp_path
):
    path = create_versioned_db(
        tmp_path / "open.db",
        patient_name="Paciente A",
        surname="Prueba",
        request_number="OPEN-A",
        analysis_date="2026-01-10",
        leucocytes=4.25,
    )
    sid = _open(isolated_api, path)

    assert isolated_api.get(f"/patient?{session_query(sid)}").json() == {
        "display_name": "Paciente A Prueba"
    }
    series = isolated_api.get(
        f"/series?param=leucocitos&{session_query(sid)}"
    )
    assert series.status_code == 200
    assert series.json()["points"] == [
        {"date": "2026-01-10", "value": 4.25}
    ]
    assert isolated_api.delete(f"/sessions/{sid}").status_code == 200


def test_uploaded_database_can_be_queried_and_closed(
    isolated_api, tmp_path
):
    source = create_versioned_db(
        tmp_path / "upload-source.db",
        patient_name="Paciente Upload",
        request_number="UPLOAD",
        analysis_date="2026-02-02",
        leucocytes=7.75,
    )
    with source.open("rb") as database:
        uploaded = isolated_api.post(
            "/sessions/upload",
            files={"db_file": ("patient.db", database, "application/octet-stream")},
        )
    assert uploaded.status_code == 200, uploaded.text
    sid = uploaded.json()["session_id"]
    assert isolated_api.get(f"/patient?{session_query(sid)}").json() == {
        "display_name": "Paciente Upload"
    }
    assert isolated_api.get(
        f"/series?param=leucocitos&{session_query(sid)}"
    ).json()["points"] == [{"date": "2026-02-02", "value": 7.75}]
    assert isolated_api.delete(f"/sessions/{sid}").status_code == 200


def test_missing_unknown_and_closed_session_contracts(isolated_api, tmp_path):
    assert isolated_api.get("/patient").status_code == 400
    assert isolated_api.get("/patient?session_id=unknown").status_code == 404

    sid = _open(
        isolated_api,
        create_versioned_db(tmp_path / "close.db", patient_name="Close"),
    )
    assert isolated_api.delete(f"/sessions/{sid}").status_code == 200
    assert isolated_api.get(f"/patient?{session_query(sid)}").status_code == 404


def test_two_sessions_are_isolated_for_reads_writes_and_close(
    isolated_api, tmp_path
):
    path_a = create_versioned_db(
        tmp_path / "a.db",
        patient_name="Alpha",
        request_number="A",
        analysis_date="2026-03-01",
        leucocytes=1.25,
    )
    path_b = create_versioned_db(
        tmp_path / "b.db",
        patient_name="Beta",
        request_number="B",
        analysis_date="2026-03-02",
        leucocytes=9.75,
    )
    sid_a = _open(isolated_api, path_a)
    sid_b = _open(isolated_api, path_b)

    assert isolated_api.get(f"/patient?{session_query(sid_a)}").json()[
        "display_name"
    ] == "Alpha"
    assert isolated_api.get(f"/patient?{session_query(sid_b)}").json()[
        "display_name"
    ] == "Beta"
    assert isolated_api.get(
        f"/series?param=leucocitos&{session_query(sid_a)}"
    ).json()["points"][0]["value"] == 1.25
    assert isolated_api.get(
        f"/series?param=leucocitos&{session_query(sid_b)}"
    ).json()["points"][0]["value"] == 9.75

    treatment = isolated_api.post(
        f"/treatments?{session_query(sid_a)}",
        json={"name": "Solo A", "start_date": "2026-03-01"},
    )
    assert treatment.status_code == 200
    limit = isolated_api.post(
        f"/param_limits?{session_query(sid_a)}",
        json={"param_key": "leucocitos", "value": 2.0},
    )
    assert limit.status_code == 200
    assert len(
        isolated_api.get(f"/timeline?{session_query(sid_a)}").json()[
            "treatments"
        ]
    ) == 1
    assert isolated_api.get(f"/timeline?{session_query(sid_b)}").json()[
        "treatments"
    ] == []
    assert len(
        isolated_api.get(f"/param_limits?{session_query(sid_a)}").json()[
            "limits"
        ]
    ) == 1
    assert isolated_api.get(f"/param_limits?{session_query(sid_b)}").json()[
        "limits"
    ] == []

    assert isolated_api.delete(f"/sessions/{sid_a}").status_code == 200
    assert isolated_api.get(f"/patient?{session_query(sid_a)}").status_code == 404
    assert isolated_api.get(f"/patient?{session_query(sid_b)}").status_code == 200


def test_concurrent_requests_keep_database_affinity(isolated_api, tmp_path):
    sid_a = _open(
        isolated_api,
        create_versioned_db(
            tmp_path / "concurrent-a.db",
            patient_name="Concurrent A",
            request_number="CA",
            leucocytes=3.0,
        ),
    )
    sid_b = _open(
        isolated_api,
        create_versioned_db(
            tmp_path / "concurrent-b.db",
            patient_name="Concurrent B",
            request_number="CB",
            leucocytes=8.0,
        ),
    )

    def read_repeatedly(session_id: str, expected: tuple[str, float]):
        results = []
        with TestClient(app) as thread_client:
            for _ in range(8):
                patient_response = thread_client.get(
                    f"/patient?{session_query(session_id)}"
                )
                series_response = thread_client.get(
                    f"/series?param=leucocitos&{session_query(session_id)}"
                )
                assert patient_response.status_code == 200
                assert series_response.status_code == 200
                result = (
                    patient_response.json()["display_name"],
                    series_response.json()["points"][0]["value"],
                )
                assert result == expected
                results.append(result)
        return results

    with ThreadPoolExecutor(max_workers=2) as executor:
        future_a = executor.submit(
            read_repeatedly, sid_a, ("Concurrent A", 3.0)
        )
        future_b = executor.submit(
            read_repeatedly, sid_b, ("Concurrent B", 8.0)
        )
        results_a = future_a.result()
        results_b = future_b.result()

    assert results_a == [("Concurrent A", 3.0)] * 8
    assert results_b == [("Concurrent B", 8.0)] * 8


def test_disappeared_session_database_returns_safe_410_and_other_session_works(
    isolated_api, tmp_path
):
    path_a = create_versioned_db(
        tmp_path / "gone.db", patient_name="Gone", leucocytes=1.0
    )
    path_b = create_versioned_db(
        tmp_path / "alive.db", patient_name="Alive", leucocytes=2.0
    )
    sid_a = _open(isolated_api, path_a)
    sid_b = _open(isolated_api, path_b)
    path_a.unlink()

    response = isolated_api.get(f"/patient?{session_query(sid_a)}")
    assert response.status_code == 410
    body = response.text
    assert str(path_a) not in body
    assert "Traceback" not in body
    assert isolated_api.get(f"/patient?{session_query(sid_b)}").json() == {
        "display_name": "Alive"
    }
    assert sessions.get(sid_b) is not None

    incompatible = tmp_path / "not-a-database.db"
    incompatible.mkdir()
    incompatible_sid = sessions.register(str(incompatible)).session_id
    incompatible_response = isolated_api.get(
        f"/patient?{session_query(incompatible_sid)}"
    )
    assert incompatible_response.status_code == 410
    assert str(incompatible) not in incompatible_response.text
    assert "Traceback" not in incompatible_response.text
