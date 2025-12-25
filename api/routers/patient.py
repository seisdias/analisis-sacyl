# api/routers/patient.py
# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter, Depends
from db import AnalysisDB
from api.deps import get_db

router = APIRouter(tags=["patient"])


@router.get("/patient")
def patient(db: AnalysisDB = Depends(get_db)) -> Dict[str, Any]:
    p = db.paciente.get()
    if not p:
        return {"display_name": ""}

    name = (p.get("nombre") or "").strip()
    surname = (p.get("apellidos") or "").strip()

    display = " ".join([x for x in [name, surname] if x]).strip()
    return {"display_name": display}
