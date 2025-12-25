# api/routers/imports.py
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from db import AnalysisDB

from api.deps import get_db, uploads_dir
from api.models import ImportPathsRequest, ImportResult

from lab_pdf import parse_hematology_pdf  # tu parser

router = APIRouter(prefix="/imports", tags=["imports"])


def _import_pdf_into_db(
        pdf_path: str,
        db: AnalysisDB = Depends(get_db)) -> None:
    data = parse_hematology_pdf(str(pdf_path))

    paciente = data.get("paciente")
    if isinstance(paciente, dict):
        db.save_patient(paciente)

    for d in data.get("hematologia", []):
        db.insert_hematologia(d)
    for d in data.get("bioquimica", []):
        db.insert_bioquimica(d)
    for d in data.get("gasometria", []):
        db.insert_gasometria(d)
    for d in data.get("orina", []):
        db.insert_orina(d)


@router.post("/from_paths", response_model=ImportResult)
def import_from_paths(
    req: ImportPathsRequest,
    db: AnalysisDB = Depends(get_db),
):
    ok = 0
    errors: List[str] = []

    for p in req.pdf_paths:
        try:
            _import_pdf_into_db(p, db)
            ok += 1
        except Exception as e:
            errors.append(f"{Path(p).name}: {e}")

    return ImportResult(ok=ok, errors=errors)


@router.post("/upload", response_model=ImportResult)
async def import_upload(
    pdf_files: List[UploadFile] = File(...),
    db: AnalysisDB = Depends(get_db),
):
    updir = uploads_dir()
    ok = 0
    errors: List[str] = []

    for uf in pdf_files:
        try:
            dest = updir / uf.filename
            content = await uf.read()
            dest.write_bytes(content)

            _import_pdf_into_db(str(dest), db)
            ok += 1
        except Exception as e:
            errors.append(f"{uf.filename}: {e}")

    return ImportResult(ok=ok, errors=errors)
