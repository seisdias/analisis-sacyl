import os
import sys
from pathlib import Path

# Asegura que el root del repo está en sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Backend headless para matplotlib
os.environ.setdefault("MPLBACKEND", "Agg")
