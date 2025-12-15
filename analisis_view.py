# analisis_view.py
"""
Compat shim (deprecated):

Se mantiene este módulo para no romper imports existentes:
    from analisis_view import AnalisisView

La implementación real está en:
    views.analisis_view_tk
"""
import warnings

warnings.warn(
    "analisis_view.py está deprecado. Usa `from views.analisis_view_tk import AnalisisView`.",
    DeprecationWarning,
    stacklevel=2,
)

from views.analisis_view_tk import AnalisisView

__all__ = ["AnalisisView"]
