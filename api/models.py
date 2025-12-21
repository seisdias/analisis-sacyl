# api/models.py
# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class OpenSessionRequest(BaseModel):
    db_path: str


class OpenSessionResponse(BaseModel):
    session_id: str
    db_path: str


class NewSessionRequest(BaseModel):
    db_path: str
    overwrite: bool = False


class ImportPathsRequest(BaseModel):
    session_id: str
    pdf_paths: List[str]


class ImportResult(BaseModel):
    ok: int
    errors: List[str]


class TreatmentCreate(BaseModel):
    name: Optional[str] = None
    start_date: Optional[str] = None   # YYYY-MM-DD
    end_date: Optional[str] = None     # YYYY-MM-DD
    standard_days: Optional[int] = None
    notes: Optional[str] = None


class TreatmentUpdate(TreatmentCreate):
    pass


class HospitalStayCreate(BaseModel):
    admission_date: Optional[str] = None
    discharge_date: Optional[str] = None
    notes: Optional[str] = None


class HospitalStayUpdate(HospitalStayCreate):
    pass


class ConfigUpdate(BaseModel):
    treatment_default_days: int = Field(..., ge=1, le=365)


class ParamLimitCreate(BaseModel):
    param_key: str
    value: float
    label: Optional[str] = None
    enabled: int = 1


class ParamLimitUpdate(ParamLimitCreate):
    pass
