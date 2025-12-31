# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Protocol, Optional, runtime_checkable, Any


@runtime_checkable
class ChartsView(Protocol):
    """Contrato mínimo que la app necesita para una vista de gráficas."""

    def set_db(self, db: Any) -> None: ...
    def set_ranges_manager(self, ranges_manager: Any) -> None: ...
    def refresh(self) -> None: ...
    def clear(self) -> None: ...


class ChartsViewFactory(Protocol):
    """Factory para crear una vista de gráficas sustituible."""

    def create(self, master: Any, *, db: Optional[Any] = None, ranges_manager: Optional[Any] = None) -> ChartsView: ...
