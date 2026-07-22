# api/routers/imports.py
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, File, UploadFile
from db import AnalysisDB

from api.deps import get_db, uploads_dir
from api.models import ImportPathsRequest, ImportResult

from lab_pdf import parse_hematology_pdf  # tu parser

router = APIRouter(prefix="/imports", tags=["imports"])

_UPLOAD_CHUNK_SIZE = 1024 * 1024
_COMPONENTS = ("hematologia", "bioquimica", "gasometria", "orina")
_METADATA_KEYS = {"fecha_analisis", "numero_peticion", "origen", "analisis_id"}


def _has_useful_values(data: dict, *, ignored: set[str] | None = None) -> bool:
    ignored = ignored or set()

    def is_useful(value) -> bool:
        if value is None:
            return False
        if isinstance(value, str):
            return bool(value.strip())
        if isinstance(value, (bytes, list, tuple, dict, set)):
            return bool(value)
        return True

    return any(key not in ignored and is_useful(value) for key, value in data.items())


def _safe_import_error(error: Exception, *paths: Path | None) -> str:
    message = str(error) or error.__class__.__name__
    for path in paths:
        if path is not None:
            message = message.replace(str(path), "archivo temporal")
            message = message.replace(str(path.resolve()), "archivo temporal")
    return message


def _best_effort_unlink(path: Path | None) -> None:
    if path is None:
        return
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def _validated_component_records(data: dict) -> dict[str, list[dict]]:
    records: dict[str, list[dict]] = {}
    has_component_data = False

    for component in _COMPONENTS:
        component_records = data.get(component, [])
        if not isinstance(component_records, list):
            raise ValueError(f"Componente {component} inválido")

        records[component] = []
        for record in component_records:
            if not isinstance(record, dict):
                raise ValueError(f"Componente {component} inválido")
            if not record.get("fecha_analisis"):
                raise ValueError("Falta fecha_analisis")
            if not record.get("numero_peticion"):
                raise ValueError("Falta numero_peticion")
            records[component].append(record)
            has_component_data |= _has_useful_values(record, ignored=_METADATA_KEYS)

    if not has_component_data:
        raise ValueError("El PDF no contiene componentes de laboratorio con datos")
    return records


def _import_pdf_into_db(
        pdf_path: str,
        db: AnalysisDB = Depends(get_db)) -> None:
    data = parse_hematology_pdf(str(pdf_path))
    records = _validated_component_records(data)

    paciente = data.get("paciente")
    if paciente is not None and not isinstance(paciente, dict):
        raise ValueError("Datos de paciente inválidos")

    conn = db.conn
    if conn is None:
        raise RuntimeError("La base de datos no está abierta")

    try:
        conn.execute("BEGIN")
        if isinstance(paciente, dict) and _has_useful_values(paciente):
            db.save_patient(paciente, commit=False)

        for d in records["hematologia"]:
            db.insert_hematologia(d, commit=False)
        for d in records["bioquimica"]:
            db.insert_bioquimica(d, commit=False)
        for d in records["gasometria"]:
            db.insert_gasometria(d, commit=False)
        for d in records["orina"]:
            db.insert_orina(d, commit=False)
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise


async def _store_pdf_upload(upload: UploadFile, destination: Path) -> None:
    first_chunk = await upload.read(_UPLOAD_CHUNK_SIZE)
    if not first_chunk.startswith(b"%PDF-"):
        raise ValueError("El contenido no es un PDF válido")

    with destination.open("xb") as output:
        output.write(first_chunk)
        while chunk := await upload.read(_UPLOAD_CHUNK_SIZE):
            output.write(chunk)


@router.post("/from_paths", response_model=ImportResult)
def import_from_paths(
    req: ImportPathsRequest,
    db: AnalysisDB = Depends(get_db),
):
    imported = 0
    errors: List[str] = []

    for p in req.pdf_paths:
        try:
            _import_pdf_into_db(p, db)
            imported += 1
        except Exception as e:
            source_path = Path(p)
            errors.append(f"{source_path.name}: {_safe_import_error(e, source_path)}")

    return ImportResult(imported=imported, errors=errors)


@router.post("/upload", response_model=ImportResult)
async def import_upload(
    pdf_files: List[UploadFile] = File(...),
    db: AnalysisDB = Depends(get_db),
):
    updir = uploads_dir()
    imported = 0
    errors: List[str] = []

    for uf in pdf_files:
        original_name = uf.filename or ""
        dest: Path | None = None
        try:
            if not original_name.strip():
                raise ValueError("Falta el nombre del archivo")
            if Path(original_name).suffix.lower() != ".pdf":
                raise ValueError("Extensión no válida (esperado .pdf)")

            dest = updir / f"{uuid4().hex}.pdf"
            await _store_pdf_upload(uf, dest)
            _import_pdf_into_db(str(dest), db)
            imported += 1
        except Exception as e:
            display_name = Path(original_name).name or "archivo sin nombre"
            errors.append(f"{display_name}: {_safe_import_error(e, dest, updir)}")
        finally:
            _best_effort_unlink(dest)
            try:
                await uf.close()
            except Exception:
                pass

    return ImportResult(imported=imported, errors=errors)
