# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Optional, Any
from .api import ChartsViewFactory, ChartsView
from .view_tk import TkChartsView


class DefaultChartsFactory:
    """Factory por defecto (TkChartsView)."""

    def create(self, master: Any, *, db: Optional[Any] = None, ranges_manager: Optional[Any] = None) -> ChartsView:
        return TkChartsView(master, db=db, ranges_manager=ranges_manager)
