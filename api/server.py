# api/server.py
# -*- coding: utf-8 -*-
from __future__ import annotations

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any, List

from charts.defs import PARAM_DEFS, PARAM_GROUPS  # fuente de verdad :contentReference[oaicite:2]{index=2}
from charts.series_provider import DbSeriesProvider  # acceso a series agnóstico de UI :contentReference[oaicite:3]{index=3}

app = FastAPI(title="salud_v1 API", version="0.2")

from fastapi.staticfiles import StaticFiles
from pathlib import Path
from pathlib import Path
from db import AnalysisDB


WEB_DIR = Path(__file__).resolve().parents[1] / "web"
app.mount("/web", StaticFiles(directory=str(WEB_DIR)), name="web")



def set_db_path(db_path: str) -> None:
    app.state.db_path = db_path

def _get_db() -> AnalysisDB:
    db_path = getattr(app.state, "db_path", None)
    if not db_path:
        raise RuntimeError("DB path no inicializado en el API (set_db_path no llamado)")

    # Abrimos una conexión propia para este hilo (seguro con SQLite)
    db = AnalysisDB(str(db_path))
    db.open()
    return db


@app.get("/")
def root() -> Dict[str, Any]:
    return {
        "name": "salud_v1 API",
        "endpoints": ["/health", "/meta", "/series?param=hemoglobina"],
    }


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/meta")
def meta() -> Dict[str, Any]:
    """
    Metadatos para el frontend:
    - defs: parámetros disponibles (tabla, label)
    - groups: agrupaciones (categorías)
    """
    return {
        "defs": PARAM_DEFS,
        "groups": [{"name": name, "params": params} for (name, params) in PARAM_GROUPS],
    }


@app.get("/series")
def series(
    param: str = Query(..., description="Nombre de parámetro (key de PARAM_DEFS)"),
    limit: int = Query(1000, ge=1, le=10000, description="Máximo de puntos"),
) -> JSONResponse:
    """
    Devuelve serie temporal ya parseada y ordenada.

    Nota: DbSeriesProvider devuelve SeriesPoint(date: datetime, value: float).
    Para el frontend lo convertimos a JSON con date ISO YYYY-MM-DD y value float.
    """
    if param not in PARAM_DEFS:
        return JSONResponse({"error": f"param desconocido: {param}"}, status_code=400)

    db = _get_db()
    try:
        provider = DbSeriesProvider(db, param_defs=PARAM_DEFS)

        if not provider.is_ready():
            return JSONResponse({"error": "DB no lista o no abierta"}, status_code=409)

        points = provider.get_series(param, limit=limit)
    finally:
        try:
            db.close()
        except Exception:
            pass

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
