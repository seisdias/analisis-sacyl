# api/routers/sessions.py
# -*- coding: utf-8 -*-
from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File

from api.deps import sessions
from api.models import OpenSessionRequest, OpenSessionResponse, NewSessionRequest
from db import AnalysisDB

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("/open", response_model=OpenSessionResponse)
def sessions_open(req: OpenSessionRequest):
    try:
        info = sessions.open_existing(req.db_path)
        return OpenSessionResponse(session_id=info.session_id, db_path=info.db_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="DB no encontrada")


@router.post("/new", response_model=OpenSessionResponse)
def sessions_new(req: NewSessionRequest):
    """
    Crea una BD nueva (si no existe) inicializando el schema con AnalysisDB,
    y registra sesión. Si ya existe, NO sobrescribe: devuelve 409.
    """
    p = Path(req.db_path).expanduser()

    # seguridad básica
    if p.suffix.lower() not in (".db", ".sqlite", ".sqlite3"):
        raise HTTPException(status_code=400, detail="Extensión no válida (esperado .db/.sqlite/.sqlite3)")

    if p.exists():
        if not getattr(req, "overwrite", False):
            raise HTTPException(status_code=409, detail="La BD ya existe (no se sobrescribe)")

        # overwrite=True -> borrar y recrear
        try:
            p.unlink()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"No se pudo sobrescribir (borrado falló): {e}")

    try:
        p.parent.mkdir(parents=True, exist_ok=True)

        # crea e inicializa schema
        db = AnalysisDB(str(p))
        db.open()
        db.close()

        # registra la sesión sobre el path recién creado
        info = sessions.register(str(p))
        return OpenSessionResponse(session_id=info.session_id, db_path=info.db_path)

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"No se pudo crear la BD: {e}")


@router.delete("/{session_id}")
def sessions_close(session_id: str):
    ok = sessions.close(session_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    return {"ok": True}


@router.post("/upload", response_model=OpenSessionResponse)
def sessions_upload(db_file: UploadFile = File(...)):
    """
    Subida de un .db desde el navegador (fallback cuando no hay pywebview).
    Guarda el fichero en ./data/uploads y abre sesión.
    """
    if not db_file.filename:
        raise HTTPException(status_code=400, detail="Fichero inválido")

    name = Path(db_file.filename).name
    if not name.lower().endswith((".db", ".sqlite", ".sqlite3")):
        raise HTTPException(status_code=400, detail="Extensión no válida")

    upload_dir = Path("data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)

    dest = upload_dir / name

    try:
        with dest.open("wb") as f:
            shutil.copyfileobj(db_file.file, f)
    finally:
        try:
            db_file.file.close()
        except Exception:
            pass

    info = sessions.open_existing(str(dest))
    return OpenSessionResponse(session_id=info.session_id, db_path=info.db_path)





