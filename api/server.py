# api/server.py
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, Query
import os
import uuid
from datetime import datetime


from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from api.session_store import SessionStore
from charts.defs import PARAM_DEFS, PARAM_GROUPS
from charts.series_provider import DbSeriesProvider
from db import AnalysisDB
from ranges import RangesManager

app = FastAPI(title="salud_v1 API", version="0.2")

# -------------------------
# Static web (dashboard)
# -------------------------
WEB_DIR = Path(__file__).resolve().parents[1] / "web"
app.mount("/web", StaticFiles(directory=str(WEB_DIR)), name="web")

# -------------------------
# Sessions
# -------------------------
sessions = SessionStore()

def _data_dir() -> Path:
    # Portable-friendly: si defines SALUD_V1_DATA_DIR, lo usamos.
    # Si no, usamos carpeta de usuario (Windows/Mac).
    base = os.getenv("SALUD_V1_DATA_DIR")
    if base:
        return Path(base).expanduser().resolve()
    return (Path.home() / ".salud_v1").resolve()

def _uploads_dir() -> Path:
    d = _data_dir() / "uploads"
    d.mkdir(parents=True, exist_ok=True)
    return d


class OpenSessionRequest(BaseModel):
    db_path: str


class OpenSessionResponse(BaseModel):
    session_id: str
    db_path: str

@app.post("/sessions/upload", response_model=OpenSessionResponse)
async def sessions_upload(db_file: UploadFile = File(...)):
    """
    Recibe una BD SQLite (multipart/form-data), la guarda en carpeta de trabajo,
    y abre una sesión contra esa copia.
    """
    filename = db_file.filename or "paciente.db"
    low = filename.lower()

    if not (low.endswith(".db") or low.endswith(".sqlite") or low.endswith(".sqlite3")):
        raise HTTPException(status_code=400, detail="Formato no soportado (esperado .db/.sqlite/.sqlite3)")

    uploads = _uploads_dir()

    # Nombre único para evitar colisiones
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(c for c in filename if c.isalnum() or c in ("-", "_", ".", " ")).strip()
    if not safe_name:
        safe_name = "paciente.db"

    out_path = uploads / f"{stamp}_{uuid.uuid4().hex}_{safe_name}"

    try:
        # Guardamos en streaming
        with out_path.open("wb") as f:
            while True:
                chunk = await db_file.read(1024 * 1024)  # 1MB
                if not chunk:
                    break
                f.write(chunk)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"No se pudo guardar la BD subida: {e}")

    # Abrimos sesión con la copia
    try:
        info = sessions.open_existing(str(out_path))
        return OpenSessionResponse(session_id=info.session_id, db_path=info.db_path)
    except Exception as e:
        # Si la BD está corrupta o no es SQLite, lo normal es fallar aquí
        try:
            out_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise HTTPException(status_code=400, detail=f"No se pudo abrir la BD subida: {e}")



@app.post("/sessions/open", response_model=OpenSessionResponse)
def sessions_open(req: OpenSessionRequest):
    try:
        info = sessions.open_existing(req.db_path)
        return OpenSessionResponse(session_id=info.session_id, db_path=info.db_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="DB no encontrada")


@app.delete("/sessions/{session_id}")
def sessions_close(session_id: str):
    ok = sessions.close(session_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    return {"ok": True}


class NewSessionRequest(BaseModel):
    db_path: str
    overwrite: bool = False  # lo dejamos listo para futuro, por ahora puedes ignorarlo


@app.post("/sessions/new", response_model=OpenSessionResponse)
def sessions_new(req: NewSessionRequest):
    import os
    from pathlib import Path

    db_path = str(Path(req.db_path).resolve())

    if os.path.exists(db_path) and not req.overwrite:
        raise HTTPException(status_code=409, detail="El archivo ya existe")

    # Si overwrite=true, borramos antes (como legacy)
    if os.path.exists(db_path) and req.overwrite:
        try:
            os.remove(db_path)
        except OSError as e:
            raise HTTPException(status_code=500, detail=f"No se pudo borrar el archivo existente: {e}")

    # Crear la BD (tu core se encarga de schema al open)
    try:
        db = AnalysisDB(db_path)
        db.open()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"No se pudo crear la BD: {e}")
    finally:
        try:
            db.close()
        except Exception:
            pass

    # Abrir sesión sobre esa BD recién creada
    info = sessions.open_existing(db_path)
    return OpenSessionResponse(session_id=info.session_id, db_path=info.db_path)



# -------------------------
# Legacy compatibility (Tkinter launcher)
# -------------------------
def set_db_path(db_path: str) -> None:
    """
    Modo legacy: el launcher (Tkinter/WebChartsLauncher) fija un db_path global.
    El API seguirá funcionando sin session_id si esto está configurado.
    """
    app.state.db_path = db_path


def _resolve_db_path(session_id: Optional[str]) -> str:
    # 1) modo sesiones
    if session_id:
        info = sessions.get(session_id)
        if not info:
            raise HTTPException(status_code=404, detail="Sesión no encontrada")
        return info.db_path

    # 2) modo legacy (Tkinter launcher)
    db_path = getattr(app.state, "db_path", None)
    if not db_path:
        raise HTTPException(
            status_code=400,
            detail="DB no configurada (falta set_db_path o session_id)",
        )
    return str(db_path)


def _get_db_for_request(session_id: Optional[str]) -> AnalysisDB:
    """
    Abre una conexión SQLite nueva para cada request (patrón seguro en FastAPI).
    """
    db_path = _resolve_db_path(session_id)
    db = AnalysisDB(db_path)
    db.open()
    return db


# -------------------------
# Basic endpoints
# -------------------------
@app.get("/")
def root() -> Dict[str, Any]:
    return {
        "name": "salud_v1 API",
        "endpoints": [
            "/health",
            "/meta",
            "/series?param=hemoglobina",
            "/ranges",
            "/sessions/open",
        ],
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


@app.get("/patient")
def patient(
    session_id: str = Query(..., description="ID de sesión (multi-paciente)"),
) -> Dict[str, Any]:
    db = _get_db_for_request(session_id)
    try:
        # Usamos el core tal cual: db.paciente.get()
        p = db.paciente.get()  # -> dict con columnas o None
        if not p:
            return {"display_name": None, "patient": None}

        nombre = (p.get("nombre") or "").strip()
        apellidos = (p.get("apellidos") or "").strip()
        display_name = " ".join([x for x in [nombre, apellidos] if x]).strip() or None

        return {
            "display_name": display_name,
            "patient": p,
        }
    finally:
        try:
            db.close()
        except Exception:
            pass



# -------------------------
# Data endpoints (now session-aware)
# -------------------------
@app.get("/series")
def series(
    param: str = Query(..., description="Nombre de parámetro (key de PARAM_DEFS)"),
    limit: int = Query(1000, ge=1, le=10000, description="Máximo de puntos"),
    session_id: Optional[str] = Query(default=None, description="ID de sesión (multi-paciente)"),
) -> JSONResponse:
    """
    Devuelve serie temporal ya parseada y ordenada.

    Nota: DbSeriesProvider devuelve SeriesPoint(date: datetime, value: float).
    Para el frontend lo convertimos a JSON con date ISO YYYY-MM-DD y value float.
    """
    if param not in PARAM_DEFS:
        return JSONResponse({"error": f"param desconocido: {param}"}, status_code=400)

    db = _get_db_for_request(session_id)
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


@app.get("/ranges")
def ranges(
    session_id: Optional[str] = Query(default=None, description="ID de sesión (multi-paciente)"),
) -> Dict[str, Any]:
    """
    Devuelve rangos de referencia por parámetro (min/max, unidad, etc.).
    No depende de la BD, pero dejamos session_id por simetría/contrato (y futuras reglas por sexo/edad).
    """
    rm = RangesManager()
    all_ranges = rm.get_all()

    out: Dict[str, Any] = {}
    for key, pr in all_ranges.items():
        out[key] = {
            "label": pr.label,
            "category": pr.category,
            "unit": pr.unit,
            "min": pr.min_value,
            "max": pr.max_value,
        }

    return {"ranges": out}
