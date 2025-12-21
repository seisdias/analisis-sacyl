# api/routers/core.py
# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter

router = APIRouter(tags=["core"])


@router.get("/")
def root() -> Dict[str, Any]:
    return {
        "name": "salud_v1 API",
        "endpoints": ["/health", "/meta", "/series?param=hemoglobina"],
    }


@router.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}
