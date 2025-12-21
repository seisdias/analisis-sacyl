# api/server.py
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from api.routers.core import router as core_router
from api.routers.sessions import router as sessions_router
from api.routers.imports import router as imports_router
from api.routers.charts import router as charts_router
from api.routers.patient import router as patient_router
from api.routers.timeline import router as timeline_router
from api.routers.limits import router as limits_router
from api.deps import sessions  # <- usar el singleton único


app = FastAPI(title="salud_v1 API", version="0.2")

WEB_DIR = Path(__file__).resolve().parents[1] / "web"
app.mount("/web", StaticFiles(directory=str(WEB_DIR)), name="web")

app.include_router(core_router)
app.include_router(sessions_router)
app.include_router(imports_router)
app.include_router(charts_router)
app.include_router(patient_router)
app.include_router(timeline_router)
app.include_router(limits_router)


