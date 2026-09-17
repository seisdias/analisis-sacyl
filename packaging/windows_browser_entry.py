from __future__ import annotations

import sys

from app.web_main import main


if __name__ == "__main__":
    args = sys.argv[1:] or ["--browser"]
    raise SystemExit(main(args))
