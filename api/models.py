# api/models.py
# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import date
import re
from typing import Optional, List

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _validate_optional_iso_date(value: Optional[str]) -> Optional[str]:
    if value is None or value == "":
        return value
    if not _ISO_DATE_RE.fullmatch(value):
        raise ValueError("La fecha debe tener formato YYYY-MM-DD")
    try:
        date.fromisoformat(value)
    except ValueError as error:
        raise ValueError("La fecha no es válida") from error
    return value


class OpenSessionRequest(BaseModel):
    db_path: str


class OpenSessionResponse(BaseModel):
    session_id: str
    db_path: str


class NewSessionRequest(BaseModel):
    db_path: str
    overwrite: bool = False


class ImportPathsRequest(BaseModel):
    pdf_paths: List[str]


class ImportResult(BaseModel):
    imported: int
    errors: List[str]


class TreatmentCreate(BaseModel):
    name: Optional[str] = None
    start_date: Optional[str] = None   # YYYY-MM-DD
    end_date: Optional[str] = None     # YYYY-MM-DD
    standard_days: Optional[int] = None
    notes: Optional[str] = None

    _validate_dates = field_validator("start_date", "end_date")(
        _validate_optional_iso_date
    )

    @model_validator(mode="after")
    def validate_date_order(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("start_date no puede ser posterior a end_date")
        return self


class TreatmentUpdate(TreatmentCreate):
    pass


class HospitalStayCreate(BaseModel):
    admission_date: Optional[str] = None
    discharge_date: Optional[str] = None
    notes: Optional[str] = None

    _validate_dates = field_validator("admission_date", "discharge_date")(
        _validate_optional_iso_date
    )

    @model_validator(mode="after")
    def validate_date_order(self):
        if (
            self.admission_date
            and self.discharge_date
            and self.admission_date > self.discharge_date
        ):
            raise ValueError(
                "admission_date no puede ser posterior a discharge_date"
            )
        return self


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

class RangeUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    min: Optional[float] = None
    max: Optional[float] = None
