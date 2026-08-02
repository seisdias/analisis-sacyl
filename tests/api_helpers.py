from __future__ import annotations

from pathlib import Path
from typing import Any

from db import AnalysisDB


def create_versioned_db(
    path: Path,
    *,
    patient_name: str | None = None,
    surname: str | None = None,
    request_number: str = "REQ-1",
    analysis_date: str = "2026-01-01",
    leucocytes: float | None = None,
    glucose: float | None = None,
) -> Path:
    """Create and seed a versioned database exclusively at the caller's path."""
    db = AnalysisDB(str(path))
    db.create()
    try:
        if patient_name is not None:
            db.save_patient(
                {
                    "nombre": patient_name,
                    "apellidos": surname,
                    "numero_historia": f"H-{request_number}",
                }
            )

        common: dict[str, Any] = {
            "fecha_analisis": analysis_date,
            "numero_peticion": request_number,
            "origen": "TEST",
        }
        if leucocytes is not None:
            db.insert_hematologia(
                {
                    **common,
                    "leucocitos": leucocytes,
                    "vcm": 90.0,
                    "rdw": 12.0,
                    "plaquetas": 180.0,
                    "vpm": 9.0,
                    "neutrofilos_pct": 50.0,
                    "linfocitos_pct": 35.0,
                    "monocitos_pct": 8.0,
                    "eosinofilos_pct": 5.0,
                    "basofilos_pct": 2.0,
                    "neutrofilos_abs": 2.5,
                    "linfocitos_abs": 1.75,
                    "monocitos_abs": 0.4,
                    "eosinofilos_abs": 0.25,
                    "basofilos_abs": 0.1,
                }
            )
        if glucose is not None:
            db.insert_bioquimica({**common, "glucosa": glucose})
    finally:
        db.close()
    return path


def session_query(session_id: str) -> str:
    return f"session_id={session_id}"
