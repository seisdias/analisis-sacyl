# -*- coding: utf-8 -*-
from __future__ import annotations
import re

def normalize_pdf_text(texto: str) -> str:
    if not texto:
        return ""

    t = texto.replace("\u00A0", " ")          # NBSP
    t = t.replace("*", " * ")                 # separa ** -> * *
    t = re.sub(r"[ \t]+", " ", t)             # colapsa espacios
    t = t.replace("\r\n", "\n").replace("\r", "\n")
    t = re.sub(r"\n{2,}", "\n", t)
    return t
