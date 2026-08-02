from __future__ import annotations

import os
import sys
from pathlib import Path


def resource_root() -> Path:
    """Root for bundled, read-only application resources."""
    frozen_root = getattr(sys, "_MEIPASS", None)
    if frozen_root:
        return Path(frozen_root).resolve()
    return Path(__file__).resolve().parents[1]


def web_root() -> Path:
    return resource_root() / "web"


def data_root() -> Path:
    """Stable writable root. This function does not create it."""
    configured = os.getenv("ANALISIS_SACYL_DATA_DIR") or os.getenv("SALUD_V1_DATA_DIR")
    if configured:
        return Path(configured).expanduser().resolve()
    return (Path.home() / ".analisis-sacyl").resolve()


def _ensure_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def pdf_uploads_dir() -> Path:
    return _ensure_directory(data_root() / "uploads" / "pdfs")


def database_uploads_dir() -> Path:
    return _ensure_directory(data_root() / "uploads" / "databases")


def runtime_temp_dir() -> Path:
    return _ensure_directory(data_root() / "tmp")


def default_database_path() -> Path:
    return data_root() / "analisis.db"
