# app/web_main.py
# -*- coding: utf-8 -*-
from __future__ import annotations

import uvicorn

from api.server import app


def main() -> None:
    # Modo “UI moderna”: un único servidor local
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info",
        reload=False,
    )


if __name__ == "__main__":
    main()
