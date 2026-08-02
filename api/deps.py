# api/deps.py
# -*- coding: utf-8 -*-
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Generator

from fastapi import HTTPException, Query, Request

from api.session_store import SessionStore
from db import AnalysisDB
from app.paths import data_root, pdf_uploads_dir


# Singleton de sesiones para toda la app
sessions = SessionStore()


def set_db_path(app, db_path: str) -> None:
    """Modo legacy: permite fijar una BD global en app.state.db_path."""
    app.state.db_path = db_path


def resolve_db_path(request: Request, session_id: Optional[str]) -> str:
    # 1) modo sesiones
    if session_id:
        info = sessions.get(session_id)
        if not info:
            raise HTTPException(status_code=404, detail="Sesión no encontrada")
        return info.db_path

    # 2) modo legacy
    db_path = getattr(request.app.state, "db_path", None)
    if not db_path:
        raise HTTPException(
            status_code=400,
            detail="DB no configurada (falta session_id y no hay db_path legacy)",
        )
    return str(db_path)


def get_db(
    request: Request,
    session_id: Optional[str] = Query(default=None),
) -> Generator[AnalysisDB, None, None]:
    """Dependency: abre DB y la cierra siempre al terminar el request."""
    db_path = resolve_db_path(request, session_id)
    if session_id and (
        not os.path.isfile(db_path)
        or not os.access(db_path, os.R_OK | os.W_OK)
    ):
        raise HTTPException(
            status_code=410,
            detail="La base de datos de la sesión ya no está disponible",
        )

    db = AnalysisDB(db_path)
    try:
        try:
            db.open()
        except (FileNotFoundError, PermissionError):
            if session_id:
                raise HTTPException(
                    status_code=410,
                    detail="La base de datos de la sesión ya no está disponible",
                )
            raise
        yield db
    finally:
        try:
            db.close()
        except Exception:
            pass


def data_dir() -> Path:
    """Compatibility wrapper for the central writable data root."""
    return data_root()


def uploads_dir() -> Path:
    """Compatibility wrapper for temporary PDF uploads."""
    return pdf_uploads_dir()
