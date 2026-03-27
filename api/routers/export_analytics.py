# api/routers/export_analytics.py
# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from db import AnalysisDB
from api.deps import get_db

router = APIRouter(tags=["export_analytics"])


CONFIG_KEY_TEMPLATE = "hematology_export_template"
DEFAULT_TEMPLATE = (
    "Analítica {fecha}: "
    "Leucocitos:{leucocitos}"
    "(Neutrófilos:{neutrofilos};Linfocitos:{linfocitos};Monocitos:{monocitos}); "
    "Hemoglobina:{hemoglobina}; "
    "Plaquetas:{plaquetas}."
)


class ExportTemplateUpdate(BaseModel):
    template: str


class ExportGenerateRequest(BaseModel):
    fecha: str


def _to_text(value: Any) -> str:
    if value is None:
        return "-"
    return str(value)


def _build_context(fecha: str, row: Dict[str, Any]) -> Dict[str, str]:
    return {
        "fecha": _to_text(fecha),
        "leucocitos": _to_text(row.get("leucocitos")),
        "neutrofilos": _to_text(row.get("neutrofilos_abs")),
        "linfocitos": _to_text(row.get("linfocitos_abs")),
        "monocitos": _to_text(row.get("monocitos_abs")),
        "hemoglobina": _to_text(row.get("hemoglobina")),
        "plaquetas": _to_text(row.get("plaquetas")),
    }


def _allowed_tokens() -> list[str]:
    return [
        "{fecha}",
        "{leucocitos}",
        "{neutrofilos}",
        "{linfocitos}",
        "{monocitos}",
        "{hemoglobina}",
        "{plaquetas}",
    ]


def _get_template(db: AnalysisDB) -> str:
    raw = db.config.config_get(CONFIG_KEY_TEMPLATE)
    if raw is None or str(raw).strip() == "":
        return DEFAULT_TEMPLATE
    return str(raw)


@router.get("/export_analytics/dates")
def list_export_dates(db: AnalysisDB = Depends(get_db)) -> Dict[str, Any]:
    fechas = db.hematologia.list_distinct_dates()
    return {
        "dates": fechas,
        "selected": fechas[0] if fechas else None,
    }


@router.get("/export_analytics/template")
def get_export_template(db: AnalysisDB = Depends(get_db)) -> Dict[str, Any]:
    template = _get_template(db)
    return {
        "template": template,
        "default_template": DEFAULT_TEMPLATE,
        "allowed_tokens": _allowed_tokens(),
    }


@router.put("/export_analytics/template")
def set_export_template(body: ExportTemplateUpdate, db: AnalysisDB = Depends(get_db)) -> Dict[str, Any]:
    template = (body.template or "").strip()
    if not template:
        raise HTTPException(status_code=400, detail="La plantilla no puede estar vacía")

    db.config.config_set(CONFIG_KEY_TEMPLATE, template)
    return {"ok": True}


@router.post("/export_analytics/generate")
def generate_export_text(body: ExportGenerateRequest, db: AnalysisDB = Depends(get_db)) -> Dict[str, Any]:
    fecha = (body.fecha or "").strip()
    if not fecha:
        raise HTTPException(status_code=400, detail="La fecha es obligatoria")

    row = db.hematologia.get_by_fecha(fecha)
    if not row:
        raise HTTPException(status_code=404, detail="No existe hematología para esa fecha")

    template = _get_template(db)
    context = _build_context(fecha, row)

    try:
        text = template.format(**context)
    except KeyError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Token no soportado en plantilla: {e.args[0]}",
        )

    return {
        "fecha": fecha,
        "template": template,
        "text": text,
        "context": context,
    }