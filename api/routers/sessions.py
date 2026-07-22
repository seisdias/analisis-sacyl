# api/routers/sessions.py
# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, HTTPException, UploadFile, File

from api.deps import sessions
from api.models import OpenSessionRequest, OpenSessionResponse, NewSessionRequest
from db import AnalysisDB

router = APIRouter(prefix="/sessions", tags=["sessions"])

SQLITE_EXTENSIONS = {".db", ".sqlite", ".sqlite3"}
SQLITE_HEADER = b"SQLite format 3\x00"
_COPY_CHUNK_SIZE = 1024 * 1024


def _best_effort_unlink(path: Path | None) -> None:
    if path is None:
        return
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def _validate_sqlite_file(path: Path, *, validate_extension: bool = True) -> Path:
    path = path.expanduser().resolve()
    if validate_extension and path.suffix.lower() not in SQLITE_EXTENSIONS:
        raise ValueError("Extensión no válida (esperado .db/.sqlite/.sqlite3)")
    if not path.exists():
        raise FileNotFoundError(path)
    if not path.is_file():
        raise ValueError("La ruta no es un archivo regular")
    with path.open("rb") as source:
        if source.read(len(SQLITE_HEADER)) != SQLITE_HEADER:
            raise ValueError("El archivo no es una base SQLite válida")
    return path


@router.post("/open", response_model=OpenSessionResponse)
def sessions_open(req: OpenSessionRequest):
    try:
        path = _validate_sqlite_file(Path(req.db_path))
        info = sessions.open_existing(str(path))
        return OpenSessionResponse(session_id=info.session_id, db_path=info.db_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="DB no encontrada")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/new", response_model=OpenSessionResponse)
def sessions_new(req: NewSessionRequest):
    """
    Crea una BD nueva (si no existe) inicializando el schema con AnalysisDB,
    y registra sesión. Si ya existe, NO sobrescribe: devuelve 409.
    """
    p = Path(req.db_path).expanduser()

    # seguridad básica
    if p.suffix.lower() not in SQLITE_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Extensión no válida (esperado .db/.sqlite/.sqlite3)")

    if p.exists() and not req.overwrite:
        raise HTTPException(status_code=409, detail="La BD ya existe (no se sobrescribe)")

    temp_path: Path | None = None
    db: AnalysisDB | None = None
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        fd, raw_temp_path = tempfile.mkstemp(
            prefix=f".{p.name}.", suffix=".tmp", dir=str(p.parent)
        )
        os.close(fd)
        temp_path = Path(raw_temp_path)

        db = AnalysisDB(str(temp_path))
        db.open()
        db.close()
        db = None

        os.replace(temp_path, p)
        temp_path = None

        info = sessions.register(str(p))
        return OpenSessionResponse(session_id=info.session_id, db_path=info.db_path)

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"No se pudo crear la BD: {e}")
    finally:
        if db is not None:
            try:
                db.close()
            except Exception:
                pass
        _best_effort_unlink(temp_path)


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

    suffix = Path(db_file.filename).suffix.lower()
    if suffix not in SQLITE_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Extensión no válida")

    upload_dir = Path("data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)

    temp_path: Path | None = None
    dest: Path | None = None
    try:
        fd, raw_temp_path = tempfile.mkstemp(
            prefix=".database-upload-", suffix=".tmp", dir=str(upload_dir)
        )
        os.close(fd)
        temp_path = Path(raw_temp_path)
        with temp_path.open("wb") as output:
            shutil.copyfileobj(db_file.file, output, length=_COPY_CHUNK_SIZE)

        _validate_sqlite_file(temp_path, validate_extension=False)
        dest = upload_dir / f"{uuid4().hex}{suffix}"
        os.replace(temp_path, dest)
        temp_path = None

        info = sessions.open_existing(str(dest))
        return OpenSessionResponse(session_id=info.session_id, db_path=info.db_path)
    except Exception as e:
        _best_effort_unlink(dest)
        if isinstance(e, ValueError):
            raise HTTPException(status_code=400, detail=str(e))
        raise HTTPException(status_code=400, detail="No se pudo cargar la BD")
    finally:
        _best_effort_unlink(temp_path)
        try:
            db_file.file.close()
        except Exception:
            pass


