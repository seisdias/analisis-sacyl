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


def _ranges_to_payload(rm: RangesManager) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for key, pr in rm.get_all().items():
        out[key] = {
            "label": pr.label,
            "category": pr.category,
            "unit": pr.unit,
            "min": pr.min_value,
            "max": pr.max_value,
        }
    return out

@router.get("/ranges")
def ranges() -> Dict[str, Any]:
    with _RM_LOCK:
        return {"ranges": _ranges_to_payload(_RM)}


@router.get("/ranges/defaults")
def ranges_defaults() -> Dict[str, Any]:
    # OJO: no tocar _RM; devolvemos defaults “fresh”
    fresh = RangesManager()
    return {"ranges": _ranges_to_payload(fresh)}


class BulkRangeUpdate(BaseModel):
    # { "leucocitos": {"min": 4.0, "max": 11.0}, ... }
    ranges: Dict[str, Dict[str, Optional[float]]]


@router.post("/ranges/bulk")
def update_ranges_bulk(body: BulkRangeUpdate) -> Dict[str, Any]:
    with _RM_LOCK:
        for key, v in body.ranges.items():
            # min/max pueden venir como null
            _RM.update_range(key, v.get("min"), v.get("max"))
        return {"ok": True, "ranges": _ranges_to_payload(_RM)}


