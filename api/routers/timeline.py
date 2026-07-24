# api/routers/timeline.py
# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, Optional
import sqlite3

from fastapi import APIRouter, Depends, HTTPException
from db import AnalysisDB
from api.deps import get_db
from api.models import (
    TreatmentCreate, TreatmentUpdate,
    HospitalStayCreate, HospitalStayUpdate,
    ConfigUpdate,
)

router = APIRouter(tags=["timeline"])


def _raise_safe_db_error() -> None:
    raise HTTPException(
        status_code=500,
        detail="No se pudo completar la operación con la base de datos",
    )


@router.get("/timeline")
def timeline(db: AnalysisDB = Depends(get_db)) -> Dict[str, Any]:
    try:
        default_days_raw = None
        if hasattr(db, "config"):
            default_days_raw = db.config.config_get("treatment_default_days")

        try:
            default_days = int(default_days_raw) if default_days_raw is not None else None
        except ValueError:
            default_days = None

        return {
            "config": {"treatment_default_days": default_days},
            "treatments": db.tratamiento.list_treatments(),
            "hospital_stays": db.ingreso.list_hospital_stays(),
        }
    except sqlite3.Error:
        _raise_safe_db_error()


@router.post("/treatments")
def create_treatment(body: TreatmentCreate, db: AnalysisDB = Depends(get_db)):
    tid = db.tratamiento.create_treatment(body.model_dump())
    return {"id": tid}


@router.put("/treatments/{treatment_id}")
def update_treatment(treatment_id: int, body: TreatmentUpdate, db: AnalysisDB = Depends(get_db)):
    if not db.tratamiento.update_treatment(treatment_id, body.model_dump()):
        raise HTTPException(status_code=404, detail="Tratamiento no encontrado")
    return {"ok": True}


@router.delete("/treatments/{treatment_id}")
def delete_treatment(treatment_id: int, db: AnalysisDB = Depends(get_db)):
    if not db.tratamiento.delete_treatment(treatment_id):
        raise HTTPException(status_code=404, detail="Tratamiento no encontrado")
    return {"ok": True}


@router.post("/hospital_stays")
def create_hospital_stay(body: HospitalStayCreate, db: AnalysisDB = Depends(get_db)):
    sid = db.ingreso.create_hospital_stay(body.model_dump())
    return {"id": sid}


@router.put("/hospital_stays/{stay_id}")
def update_hospital_stay(stay_id: int, body: HospitalStayUpdate, db: AnalysisDB = Depends(get_db)):
    if not db.ingreso.update_hospital_stay(stay_id, body.model_dump()):
        raise HTTPException(status_code=404, detail="Ingreso no encontrado")
    return {"ok": True}


@router.delete("/hospital_stays/{stay_id}")
def delete_hospital_stay(stay_id: int, db: AnalysisDB = Depends(get_db)):
    if not db.ingreso.delete_hospital_stay(stay_id):
        raise HTTPException(status_code=404, detail="Ingreso no encontrado")
    return {"ok": True}


@router.put("/config")
def update_config(body: ConfigUpdate, db: AnalysisDB = Depends(get_db)):
    # Asegúrate de que tu componente config tenga set(key,value)
    db.config.config_set("treatment_default_days", str(body.treatment_default_days))
    return {"ok": True}
