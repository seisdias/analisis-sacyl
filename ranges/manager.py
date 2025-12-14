# ranges/manager.py
from __future__ import annotations
from dataclasses import asdict
from typing import Dict, Optional, List
from .models import ParamRange
from .defaults import DEFAULT_PARAM_RANGES

class RangesManager:
    def __init__(self):
        self.reset_defaults()

    def get_all(self) -> Dict[str, ParamRange]:
        return self._ranges

    def get_by_category(self) -> Dict[str, List[ParamRange]]:
        cats: Dict[str, List[ParamRange]] = {}
        for pr in self._ranges.values():
            cats.setdefault(pr.category, []).append(pr)
        for cat in cats:
            cats[cat].sort(key=lambda r: r.label)
        return cats

    def update_range(self, key: str, min_value: Optional[float], max_value: Optional[float]) -> None:
        if key not in self._ranges:
            raise KeyError(f"Parámetro desconocido: {key}")
        pr = self._ranges[key]
        pr.min_value = min_value
        pr.max_value = max_value

    def reset_defaults(self) -> None:
        self._ranges = {k: ParamRange(**asdict(v)) for k, v in DEFAULT_PARAM_RANGES.items()}
