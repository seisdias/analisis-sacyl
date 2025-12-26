# api/routers/timeline.py
# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends
from db import AnalysisDB
from api.deps import get_db
from api.models import (
    TreatmentCreate, TreatmentUpdate,
    HospitalStayCreate, HospitalStayUpdate,
    ConfigUpdate,
)

router = APIRouter(tags=["timeline"])


@router.get("/timeline")
def timeline(db: AnalysisDB = Depends(get_db)) -> Dict[str, Any]:
    default_days_raw = None
    if hasattr(db, "config"):
        default_days_raw = db.config.config_get("treatment_default_days")

    try:
        default_days = int(default_days_raw) if default_days_raw is not None else None
    except ValueError:
        default_days = None

    return {
        "config": {"treatment_default_days": default_days},
        "treatments.js": db.tratamiento.list_treatments(),
        "hospital_stays": db.ingreso.list_hospital_stays(),
    }


@router.post("/treatments.js")
def create_treatment(body: TreatmentCreate, db: AnalysisDB = Depends(get_db)):
    tid = db.tratamiento.create_treatment(body.dict())
    return {"id": tid}


@router.put("/treatments.js/{treatment_id}")
def update_treatment(treatment_id: int, body: TreatmentUpdate, db: AnalysisDB = Depends(get_db)):
    db.tratamiento.update_treatment(treatment_id, body.dict())
    return {"ok": True}


@router.delete("/treatments.js/{treatment_id}")
def delete_treatment(treatment_id: int, db: AnalysisDB = Depends(get_db)):
    db.tratamiento.delete_treatment(treatment_id)
    return {"ok": True}


@router.post("/hospital_stays")
def create_hospital_stay(body: HospitalStayCreate, db: AnalysisDB = Depends(get_db)):
    sid = db.ingreso.create_hospital_stay(body.dict())
    return {"id": sid}


@router.put("/hospital_stays/{stay_id}")
def update_hospital_stay(stay_id: int, body: HospitalStayUpdate, db: AnalysisDB = Depends(get_db)):
    db.ingreso.update_hospital_stay(stay_id, body.dict())
    return {"ok": True}


@router.delete("/hospital_stays/{stay_id}")
def delete_hospital_stay(stay_id: int, db: AnalysisDB = Depends(get_db)):
    db.ingreso.delete_hospital_stay(stay_id)
    return {"ok": True}


@router.put("/config")
def update_config(body: ConfigUpdate, db: AnalysisDB = Depends(get_db)):
    # Asegúrate de que tu componente config tenga set(key,value)
    db.config.config_set("treatment_default_days", str(body.treatment_default_days))
    return {"ok": True}
