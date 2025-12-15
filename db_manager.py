# db_manager.py
import warnings
from db import AnalysisDB

warnings.warn(
    "db_manager.py está deprecado. Usa `from db import AnalysisDB`.",
    DeprecationWarning,
    stacklevel=2,
)

HematologyDB = AnalysisDB

__all__ = ["AnalysisDB", "HematologyDB"]
