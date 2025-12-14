# -*- coding: utf-8 -*-
"""
Compat shim: mantenemos el import antiguo `from charts_view import ChartsView`
pero la implementación real vive en `charts.charts`.
"""

from charts.view_tk import TkChartsView as ChartsView

__all__ = ["ChartsView"]
