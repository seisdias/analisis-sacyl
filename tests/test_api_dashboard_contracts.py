from __future__ import annotations

import sqlite3

import pytest
from fastapi.testclient import TestClient

from api.server import app
from db.limite_parametro import LimiteParametro
from db.tratamiento import Tratamiento
from tests.api_helpers import create_versioned_db, session_query


@pytest.fixture
def dashboard_session(isolated_api, tmp_path):
    path = create_versioned_db(
        tmp_path / "dashboard.db",
        patient_name="Dashboard",
        request_number="DASH",
        analysis_date="2026-05-10",
        leucocytes=5.5,
        glucose=91.0,
    )
    response = isolated_api.post("/sessions/open", json={"db_path": str(path)})
    assert response.status_code == 200
    return isolated_api, response.json()["session_id"]


def test_core_meta_patient_series_and_histogram_contracts(dashboard_session):
    client, sid = dashboard_session
    query = session_query(sid)

    root = client.get("/")
    assert root.status_code == 200
    assert root.json()["name"] == "salud_v1 API"
    assert "/health" in root.json()["endpoints"]
    assert client.get("/health").json() == {"status": "ok"}

    meta = client.get("/meta")
    assert meta.status_code == 200
    assert "leucocitos" in meta.json()["defs"]
    assert {"name", "params"} <= set(meta.json()["groups"][0])

    assert client.get(f"/patient?{query}").json() == {
        "display_name": "Dashboard"
    }
    series = client.get(f"/series?param=leucocitos&limit=10000&{query}")
    assert series.status_code == 200
    assert {
        "param",
        "label",
        "table",
        "points",
    } == set(series.json())
    assert series.json()["points"] == [{"date": "2026-05-10", "value": 5.5}]
    assert client.get(f"/series?param=unknown&{query}").status_code == 400
    assert client.get(f"/series?param=leucocitos&limit=0&{query}").status_code == 422
    assert (
        client.get(f"/series?param=leucocitos&limit=10001&{query}").status_code
        == 422
    )

    dates = client.get(f"/histograms/dates?{query}")
    assert dates.status_code == 200
    assert dates.json() == {"dates": ["2026-05-10"]}
    assert (
        client.get(
            f"/histograms/proxy?date=2026-05-10&type=invalid&{query}"
        ).status_code
        == 400
    )
    assert (
        client.get(
            f"/histograms/proxy?date=2020-01-01&type=rbc&{query}"
        ).status_code
        == 404
    )
    proxy = client.get(
        f"/histograms/proxy?date=2026-05-10&type=rbc&{query}"
    )
    assert proxy.status_code == 200
    assert proxy.json()["is_proxy"] is True
    assert {"x", "y", "raw"} <= set(proxy.json())


def test_timeline_crud_config_and_not_found_contract(dashboard_session):
    client, sid = dashboard_session
    query = session_query(sid)

    initial = client.get(f"/timeline?{query}")
    assert initial.status_code == 200
    assert initial.json() == {
        "config": {"treatment_default_days": None},
        "treatments": [],
        "hospital_stays": [],
    }

    treatment = client.post(
        f"/treatments?{query}",
        json={
            "name": "Inicial",
            "start_date": "2026-05-01",
            "end_date": "2026-05-05",
            "standard_days": 5,
            "notes": "",
        },
    )
    stay = client.post(
        f"/hospital_stays?{query}",
        json={
            "admission_date": "2026-05-02",
            "discharge_date": "2026-05-04",
            "notes": "Ingreso inicial",
        },
    )
    assert treatment.status_code == stay.status_code == 200
    treatment_id = treatment.json()["id"]
    stay_id = stay.json()["id"]

    current = client.get(f"/timeline?{query}").json()
    assert current["treatments"][0]["name"] == "Inicial"
    assert current["hospital_stays"][0]["notes"] == "Ingreso inicial"

    updated_treatment = client.put(
        f"/treatments/{treatment_id}?{query}",
        json={
            "name": "Modificado",
            "start_date": "2026-05-03",
            "end_date": "2026-05-07",
            "standard_days": 4,
            "notes": "Cambio",
        },
    )
    updated_stay = client.put(
        f"/hospital_stays/{stay_id}?{query}",
        json={
            "admission_date": "2026-05-03",
            "discharge_date": "2026-05-06",
            "notes": "Alta modificada",
        },
    )
    assert updated_treatment.json() == updated_stay.json() == {"ok": True}
    current = client.get(f"/timeline?{query}").json()
    assert current["treatments"][0]["name"] == "Modificado"
    assert current["hospital_stays"][0]["notes"] == "Alta modificada"

    config = client.put(
        f"/config?{query}", json={"treatment_default_days": 28}
    )
    assert config.status_code == 200
    assert client.get(f"/timeline?{query}").json()["config"] == {
        "treatment_default_days": 28
    }

    assert client.delete(f"/treatments/{treatment_id}?{query}").json() == {
        "ok": True
    }
    assert client.delete(f"/hospital_stays/{stay_id}?{query}").json() == {
        "ok": True
    }
    final = client.get(f"/timeline?{query}").json()
    assert final["treatments"] == []
    assert final["hospital_stays"] == []
    assert client.put(
        f"/treatments/999999?{query}", json={"name": "No existe"}
    ).status_code == 404
    assert client.delete(f"/treatments/999999?{query}").status_code == 404
    assert client.put(
        f"/hospital_stays/999999?{query}", json={"notes": "No existe"}
    ).status_code == 404
    assert client.delete(f"/hospital_stays/999999?{query}").status_code == 404


@pytest.mark.parametrize(
    ("endpoint", "body"),
    [
        (
            "/treatments",
            {"start_date": "2026/05/01", "end_date": "2026-05-02"},
        ),
        (
            "/treatments",
            {"start_date": "2026-02-30", "end_date": "2026-03-01"},
        ),
        (
            "/treatments",
            {"start_date": "2026-05-03", "end_date": "2026-05-02"},
        ),
        (
            "/hospital_stays",
            {
                "admission_date": "2026-05-03",
                "discharge_date": "2026-05-02",
            },
        ),
    ],
)
def test_timeline_invalid_dates_return_422(
    dashboard_session, endpoint, body
):
    client, sid = dashboard_session
    query = session_query(sid)
    post_response = client.post(f"{endpoint}?{query}", json=body)
    assert post_response.status_code == 422
    assert "Traceback" not in post_response.text

    if endpoint == "/treatments":
        created = client.post(f"/treatments?{query}", json={"name": "Válido"})
        update_path = f"/treatments/{created.json()['id']}?{query}"
    else:
        created = client.post(
            f"/hospital_stays?{query}", json={"notes": "Válido"}
        )
        update_path = f"/hospital_stays/{created.json()['id']}?{query}"
    put_response = client.put(update_path, json=body)
    assert put_response.status_code == 422
    assert "Traceback" not in put_response.text


def test_timeline_allows_valid_empty_optional_dates(dashboard_session):
    client, sid = dashboard_session
    query = session_query(sid)
    assert client.post(
        f"/treatments?{query}",
        json={"name": "Sin fecha", "start_date": "", "end_date": None},
    ).status_code == 200
    assert client.post(
        f"/hospital_stays?{query}",
        json={"admission_date": None, "discharge_date": "", "notes": ""},
    ).status_code == 200


def test_param_limits_full_crud_filter_disable_and_not_found(
    dashboard_session,
):
    client, sid = dashboard_session
    query = session_query(sid)
    assert client.get(f"/param_limits?{query}").json() == {"limits": []}

    created = client.post(
        f"/param_limits?{query}",
        json={
            "param_key": "leucocitos",
            "value": 2.5,
            "label": "Alerta",
            "enabled": 1,
        },
    )
    assert created.status_code == 200
    limit_id = created.json()["id"]
    filtered = client.get(f"/param_limits?param_key=leucocitos&{query}")
    assert filtered.status_code == 200
    assert filtered.json()["limits"][0]["value"] == 2.5

    updated = client.put(
        f"/param_limits/{limit_id}?{query}",
        json={
            "param_key": "leucocitos",
            "value": 3.5,
            "label": "Deshabilitado",
            "enabled": 0,
        },
    )
    assert updated.json() == {"ok": True}
    row = client.get(f"/param_limits?{query}").json()["limits"][0]
    assert row["value"] == 3.5
    assert row["enabled"] == 0

    assert client.delete(f"/param_limits/{limit_id}?{query}").json() == {
        "ok": True
    }
    assert client.get(f"/param_limits?{query}").json() == {"limits": []}
    valid_body = {"param_key": "x", "value": 1.0, "enabled": 1}
    assert client.put(
        f"/param_limits/999999?{query}", json=valid_body
    ).status_code == 404
    assert client.delete(f"/param_limits/999999?{query}").status_code == 404


def test_identical_updates_are_not_reported_as_missing(dashboard_session):
    client, sid = dashboard_session
    query = session_query(sid)

    treatment_body = {
        "name": "Igual",
        "start_date": "2026-05-01",
        "end_date": "2026-05-02",
        "standard_days": 2,
        "notes": "Sin cambios",
    }
    treatment = client.post(f"/treatments?{query}", json=treatment_body)
    assert client.put(
        f"/treatments/{treatment.json()['id']}?{query}",
        json=treatment_body,
    ).json() == {"ok": True}

    stay_body = {
        "admission_date": "2026-05-01",
        "discharge_date": "2026-05-02",
        "notes": "Sin cambios",
    }
    stay = client.post(f"/hospital_stays?{query}", json=stay_body)
    assert client.put(
        f"/hospital_stays/{stay.json()['id']}?{query}",
        json=stay_body,
    ).json() == {"ok": True}

    limit_body = {
        "param_key": "leucocitos",
        "value": 2.0,
        "label": "Sin cambios",
        "enabled": 1,
    }
    limit_response = client.post(f"/param_limits?{query}", json=limit_body)
    assert client.put(
        f"/param_limits/{limit_response.json()['id']}?{query}",
        json=limit_body,
    ).json() == {"ok": True}


def test_ranges_are_global_nonpersistent_and_invalid_input_is_controlled(
    isolated_api,
):
    initial = isolated_api.get("/ranges")
    defaults = isolated_api.get("/ranges/defaults")
    assert initial.status_code == defaults.status_code == 200
    assert initial.json() == defaults.json()
    assert {"label", "category", "unit", "min", "max"} <= set(
        initial.json()["ranges"]["glucosa"]
    )

    changed = isolated_api.post(
        "/ranges/bulk",
        json={"ranges": {"glucosa": {"min": 65.0, "max": 120.0}}},
    )
    assert changed.status_code == 200
    assert changed.json()["ranges"]["glucosa"]["min"] == 65.0
    assert isolated_api.get("/ranges").json()["ranges"]["glucosa"]["max"] == 120.0
    assert (
        isolated_api.get("/ranges?session_id=ignored").json()
        == isolated_api.get("/ranges").json()
    )
    assert isolated_api.get("/ranges/defaults").json() == defaults.json()

    unknown = isolated_api.post(
        "/ranges/bulk",
        json={"ranges": {"not-a-param": {"min": 1.0, "max": 2.0}}},
    )
    assert unknown.status_code == 400
    assert "Traceback" not in unknown.text
    before_atomicity_check = isolated_api.get("/ranges").json()
    mixed = isolated_api.post(
        "/ranges/bulk",
        json={
            "ranges": {
                "glucosa": {"min": 1.0, "max": 2.0},
                "not-a-param": {"min": 3.0, "max": 4.0},
            }
        },
    )
    assert mixed.status_code == 400
    assert isolated_api.get("/ranges").json() == before_atomicity_check
    malformed = isolated_api.post(
        "/ranges/bulk", json={"ranges": {"glucosa": {"min": "bad"}}}
    )
    assert malformed.status_code == 422
    unexpected_field = isolated_api.post(
        "/ranges/bulk",
        json={"ranges": {"glucosa": {"minimum": 1.0, "max": 2.0}}},
    )
    assert unexpected_field.status_code == 422


def test_invalid_json_required_types_and_path_ids_are_422(dashboard_session):
    client, sid = dashboard_session
    query = session_query(sid)
    invalid_json = client.post(
        f"/param_limits?{query}",
        content="{",
        headers={"Content-Type": "application/json"},
    )
    assert invalid_json.status_code == 422
    assert client.post(f"/param_limits?{query}", json={}).status_code == 422
    assert client.post(
        f"/param_limits?{query}",
        json={"param_key": "x", "value": "not-a-number"},
    ).status_code == 422
    assert client.delete(f"/treatments/not-an-int?{query}").status_code == 422
    assert client.delete(f"/param_limits/not-an-int?{query}").status_code == 422
    assert client.put(
        f"/config?{query}", json={"treatment_default_days": 0}
    ).status_code == 422


def test_representative_db_errors_are_safe(
    dashboard_session, monkeypatch, tmp_path
):
    client, sid = dashboard_session
    query = session_query(sid)
    sensitive = f"{tmp_path}/private.db SQL SELECT secret FROM patient"

    monkeypatch.setattr(
        Tratamiento,
        "list_treatments",
        lambda _self: (_ for _ in ()).throw(sqlite3.OperationalError(sensitive)),
    )
    timeline = client.get(f"/timeline?{query}")
    assert timeline.status_code == 500
    assert timeline.json() == {
        "detail": "No se pudo completar la operación con la base de datos"
    }
    assert sensitive not in timeline.text

    monkeypatch.setattr(
        Tratamiento,
        "create_treatment",
        lambda _self, _data: (_ for _ in ()).throw(
            sqlite3.IntegrityError(sensitive)
        ),
    )
    with TestClient(app, raise_server_exceptions=False) as safe_client:
        integrity = safe_client.post(
            f"/treatments?{query}", json={"name": "No se inserta"}
        )
    assert integrity.status_code == 500
    assert sensitive not in integrity.text
    assert "Traceback" not in integrity.text

    monkeypatch.setattr(
        LimiteParametro,
        "list_param_limits",
        lambda _self, param_key=None: (_ for _ in ()).throw(
            sqlite3.OperationalError(sensitive)
        ),
    )
    limits = client.get(f"/param_limits?{query}")
    assert limits.status_code == 500
    assert limits.json() == {"detail": "No se pudieron consultar los límites"}
    assert sensitive not in limits.text
    assert "Traceback" not in limits.text
