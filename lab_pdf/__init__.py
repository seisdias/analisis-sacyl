# -*- coding: utf-8 -*-
"""
Paquete de parsers de informes PDF de laboratorio (HURH → JSON).

Expone:
  - parse_hematology_pdf
  - pdf_to_json_file
"""

from .pdf_to_json import parse_hematology_pdf, pdf_to_json_file

__all__ = ["parse_hematology_pdf", "pdf_to_json_file"]
