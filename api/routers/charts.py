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
from charts.proxy_histograms import (
    rbc_size_distribution_proxy,
    plt_size_distribution_proxy,
    wbc_differential_proxy,
)
import re

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


@router.get("/histograms/dates")
def get_histogram_dates(db: AnalysisDB = Depends(get_db)):
    """
    Devuelve fechas (ISO YYYY-MM-DD) con analíticas de hematología disponibles.
    (Solo lectura; delega en el componente Hematologia)
    """
    dates = db.hematologia.list_distinct_dates()
    return {"dates": dates}


from fastapi import HTTPException

@router.get("/histograms/proxy")
def histogram_proxy(
    date: str = Query(..., description="Fecha ISO YYYY-MM-DD"),
    type: str = Query(..., description="Tipo de histograma: rbc | plt | wbc"),
    db: AnalysisDB = Depends(get_db),
):
    """
    Devuelve datos base para histogramas proxy (no bins reales).
    """

    if not type or type not in ("rbc", "plt", "wbc"):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_histogram_type",
                "message": "Debe seleccionar un tipo de histograma válido",
                "allowed": ["rbc", "plt", "wbc"],
            },
        )

    if not date:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "missing_date",
                "message": "Debe seleccionar una fecha con analítica disponible",
            },
        )

    ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

    if not ISO_DATE_RE.match(date):
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_date_format", "message": "Formato esperado: YYYY-MM-DD"},
        )

    h = db.hematologia.get_by_fecha(date)
    if not h:
        raise HTTPException(status_code=404, detail="No hay hematología para esa fecha")

    if type == "rbc":
        payload = rbc_size_distribution_proxy(
            vcm=h.get("vcm"),
            rdw=h.get("rdw"),
        )
        if not payload.get("ok"):
            raise HTTPException(status_code=422, detail=payload.get("reason", "No se pudo calcular proxy RBC"))

        return {
            "date": date,
            "type": type,
            "is_proxy": True,
            "raw": h,
            **payload,
        }

    if type == "plt":
        payload = plt_size_distribution_proxy(
            vpm=h.get("vpm"),
            plaquetas=h.get("plaquetas"),
        )
        if not payload.get("ok"):
            raise HTTPException(status_code=422, detail=payload.get("reason", "No se pudo calcular proxy PLT"))

        return {
            "date": date,
            "type": type,
            "is_proxy": True,
            "raw": h,
            **payload,
        }

    if type == "wbc":
        payload = wbc_differential_proxy(
            neutro_pct=h.get("neutrofilos_pct"),
            linf_pct=h.get("linfocitos_pct"),
            mono_pct=h.get("monocitos_pct"),
            eos_pct=h.get("eosinofilos_pct"),
            baso_pct=h.get("basofilos_pct"),
            neutro_abs=h.get("neutrofilos_abs"),
            linf_abs=h.get("linfocitos_abs"),
            mono_abs=h.get("monocitos_abs"),
            eos_abs=h.get("eosinofilos_abs"),
            baso_abs=h.get("basofilos_abs"),
        )
        if not payload.get("ok"):
            raise HTTPException(status_code=422, detail=payload.get("reason", "No se pudo calcular proxy WBC"))

        return {
            "date": date,
            "type": type,
            "is_proxy": True,
            "raw": h,
            **payload,
        }






