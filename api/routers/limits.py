# api/routers/limits.py
# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, Optional
import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Query
from db import AnalysisDB
from api.deps import get_db
from api.models import ParamLimitCreate, ParamLimitUpdate

router = APIRouter(tags=["limits"])


@router.get("/param_limits")
def param_limits(
    param_key: Optional[str] = Query(None),
    db: AnalysisDB = Depends(get_db),
) -> Dict[str, Any]:
    try:
        limits = db.limite_parametro.list_param_limits(param_key=param_key)
    except sqlite3.Error:
        raise HTTPException(
            status_code=500,
            detail="No se pudieron consultar los límites",
        )
    return {"limits": limits}


@router.post("/param_limits")
def create_param_limit(body: ParamLimitCreate, db: AnalysisDB = Depends(get_db)):
    lid = db.limite_parametro.create_param_limit(body.model_dump())
    return {"id": lid}


@router.put("/param_limits/{limit_id}")
def update_param_limit(limit_id: int, body: ParamLimitUpdate, db: AnalysisDB = Depends(get_db)):
    if not db.limite_parametro.update_param_limit(limit_id, body.model_dump()):
        raise HTTPException(status_code=404, detail="Límite no encontrado")
    return {"ok": True}


@router.delete("/param_limits/{limit_id}")
def delete_param_limit(limit_id: int, db: AnalysisDB = Depends(get_db)):
    if not db.limite_parametro.delete_param_limit(limit_id):
        raise HTTPException(status_code=404, detail="Límite no encontrado")
    return {"ok": True}
