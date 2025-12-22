# api/routers/charts.py
# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, List
from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from api.models import RangeUpdate
from charts.defs import PARAM_DEFS, PARAM_GROUPS
from charts.series_provider import DbSeriesProvider
from ranges import RangesManager
from db import AnalysisDB
from api.deps import get_db
from pydantic import BaseModel
from typing import Optional

router = APIRouter(tags=["charts"])

from threading import RLock
_RM_LOCK = RLock()
_RM = RangesManager()



@router.get("/meta")
def meta() -> Dict[str, Any]:
    return {
        "defs": PARAM_DEFS,
        "groups": [{"name": name, "params": params} for (name, params) in PARAM_GROUPS],
    }


@router.get("/series")
def series(
    param: str = Query(..., description="Nombre de parámetro (key de PARAM_DEFS)"),
    limit: int = Query(1000, ge=1, le=10000, description="Máximo de puntos"),
    db: AnalysisDB = Depends(get_db),
) -> JSONResponse:
    if param not in PARAM_DEFS:
        return JSONResponse({"error": f"param desconocido: {param}"}, status_code=400)

    provider = DbSeriesProvider(db, param_defs=PARAM_DEFS)
    if not provider.is_ready():
        return JSONResponse({"error": "DB no lista o no abierta"}, status_code=409)

    points = provider.get_series(param, limit=limit)

    payload_points: List[Dict[str, Any]] = [
        {"date": p.date.strftime("%Y-%m-%d"), "value": p.value} for p in points
    ]

    return JSONResponse(
        {
            "param": param,
            "label": PARAM_DEFS[param].get("label", param),
            "table": PARAM_DEFS[param].get("table"),
            "points": payload_points,
        }
    )


@router.get("/ranges")
def ranges() -> Dict[str, Any]:
    with _RM_LOCK:
        all_ranges = _RM.get_all()

    out: Dict[str, Any] = {}
    for key, pr in all_ranges.items():
        out[key] = {
            "label": pr.label,
            "category": pr.category,
            "unit": pr.unit,
            "min": pr.min_value,
            "max": pr.max_value,
        }
    return {"ranges": out}

@router.put("/ranges/{key}")
def update_range(key: str, body: RangeUpdate) -> Dict[str, Any]:
    with _RM_LOCK:
        _RM.update_range(key, body.min, body.max)
        pr = _RM.get_all()[key]
    return {
        "ok": True,
        "range": {
            "key": key,
            "label": pr.label,
            "category": pr.category,
            "unit": pr.unit,
            "min": pr.min_value,
            "max": pr.max_value,
        },
    }


@router.post("/ranges/reset")
def reset_ranges() -> Dict[str, Any]:
    with _RM_LOCK:
        _RM.reset_defaults()
    return {"ok": True}


