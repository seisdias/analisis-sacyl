# ranges/models.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

@dataclass
class ParamRange:
    key: str
    label: str
    category: str
    unit: str
    min_value: Optional[float]
    max_value: Optional[float]
