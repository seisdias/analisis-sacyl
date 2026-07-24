from __future__ import annotations

from pathlib import Path

from tests.api_helpers import create_versioned_db, session_query


DATA_DIR = Path(__file__).resolve().parent / "data"
SAMPLE_REPORT = DATA_DIR / "sample_lab_report_2025_06_24.pdf"
COMPLETE_REPORT = DATA_DIR / "hemocultivos_20251113.pdf"
UNRECOGNIZED_REPORT = DATA_DIR / "hemocultivos_20251108_hemocultivos.pdf"


def _new_session(client, path: Path) -> str:
    response = client.post("/sessions/new", json={"db_path": str(path)})
    assert response.status_code == 200, response.text
    return response.json()["session_id"]


def _dashboard_snapshot(client, sid: str) -> dict:
    query = session_query(sid)
    patient = client.get(f"/patient?{query}")
    leucocytes = client.get(f"/series?param=leucocitos&{query}")
    glucose = client.get(f"/series?param=glucosa&{query}")
    dates = client.get(f"/histograms/dates?{query}")
    for response in (patient, leucocytes, glucose, dates):
        assert response.status_code == 200, response.text
    return {
        "patient": patient.json(),
        "leucocytes": leucocytes.json()["points"],
        "glucose": glucose.json()["points"],
        "dates": dates.json()["dates"],
    }


def test_real_pdf_upload_populates_dashboard_and_all_histogram_proxies(
    isolated_api, tmp_path
):
    sid = _new_session(isolated_api, tmp_path / "pdf-upload.db")
    with SAMPLE_REPORT.open("rb") as report:
        response = isolated_api.post(
            f"/imports/upload?{session_query(sid)}",
            files={"pdf_files": (SAMPLE_REPORT.name, report, "application/pdf")},
        )

    assert response.status_code == 200
    assert response.json() == {"imported": 1, "errors": []}
    snapshot = _dashboard_snapshot(isolated_api, sid)
    assert snapshot["patient"]["display_name"].startswith("PACIENTE")
    assert snapshot["leucocytes"] == [{"date": "2025-06-24", "value": 2.4}]
    assert snapshot["glucose"] == [{"date": "2025-06-24", "value": 84.0}]
    assert snapshot["dates"] == ["2025-06-24"]
    assert list((tmp_path / "salud-data" / "uploads").iterdir()) == []

    for proxy_type in ("rbc", "plt", "wbc"):
        proxy = isolated_api.get(
            "/histograms/proxy"
            f"?date=2025-06-24&type={proxy_type}&{session_query(sid)}"
        )
        assert proxy.status_code == 200, proxy.text
        payload = proxy.json()
        assert payload["date"] == "2025-06-24"
        assert payload["type"] == proxy_type
        assert payload["is_proxy"] is True
        if proxy_type == "wbc":
            assert {"categories", "pct", "abs"} <= set(payload)
        else:
            assert {"x", "y"} <= set(payload)


def test_real_pdf_from_paths_has_same_frontend_contract_as_upload(
    isolated_api, tmp_path
):
    sid_paths = _new_session(isolated_api, tmp_path / "pdf-paths.db")
    path_response = isolated_api.post(
        f"/imports/from_paths?{session_query(sid_paths)}",
        json={"pdf_paths": [str(COMPLETE_REPORT)]},
    )
    assert path_response.status_code == 200
    assert path_response.json() == {"imported": 1, "errors": []}
    paths_snapshot = _dashboard_snapshot(isolated_api, sid_paths)
    assert paths_snapshot["patient"]["display_name"] == (
        "PACIENTE PRUEBA APELLIDO FICTICIO"
    )
    assert paths_snapshot["leucocytes"] == [
        {"date": "2025-11-13", "value": 0.4}
    ]
    assert paths_snapshot["glucose"] == [
        {"date": "2025-11-13", "value": 106.0}
    ]
    assert paths_snapshot["dates"] == ["2025-11-13"]

    sid_upload = _new_session(isolated_api, tmp_path / "pdf-equivalent.db")
    with COMPLETE_REPORT.open("rb") as report:
        upload_response = isolated_api.post(
            f"/imports/upload?{session_query(sid_upload)}",
            files={
                "pdf_files": (
                    COMPLETE_REPORT.name,
                    report,
                    "application/pdf",
                )
            },
        )
    assert upload_response.status_code == 200
    assert upload_response.json() == path_response.json()
    assert _dashboard_snapshot(isolated_api, sid_upload) == paths_snapshot
    assert list((tmp_path / "salud-data" / "uploads").iterdir()) == []


def test_unrecognized_real_pdf_is_sanitized_and_atomic(
    isolated_api, tmp_path
):
    path = create_versioned_db(
        tmp_path / "negative.db",
        patient_name="Paciente Existente",
        request_number="ORIGINAL",
        analysis_date="2026-04-01",
        leucocytes=6.5,
    )
    opened = isolated_api.post("/sessions/open", json={"db_path": str(path)})
    sid = opened.json()["session_id"]
    before = _dashboard_snapshot(isolated_api, sid)

    response = isolated_api.post(
        f"/imports/from_paths?{session_query(sid)}",
        json={"pdf_paths": [str(UNRECOGNIZED_REPORT)]},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["imported"] == 0
    assert len(payload["errors"]) == 1
    assert payload["errors"][0].startswith(f"{UNRECOGNIZED_REPORT.name}:")
    assert str(DATA_DIR) not in payload["errors"][0]
    assert "Traceback" not in payload["errors"][0]
    assert _dashboard_snapshot(isolated_api, sid) == before
