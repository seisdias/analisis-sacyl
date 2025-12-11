# tests/test_lab_pdf/conftest.py
from pathlib import Path

import pytest

from lab_pdf.pdf_utils import extract_text_from_pdf


@pytest.fixture(scope="session")
def data_dir() -> Path:
    """Directorio con los PDFs de ejemplo."""
    return Path(__file__).parents[1] / "data"


@pytest.fixture(scope="session")
def pdf_hemato_path(data_dir: Path) -> Path:
    """
    Informe completo de laboratorio:
    hematología + bioquímica + gasometría.
    """
    return data_dir / "12383248W_20251111.pdf"


@pytest.fixture(scope="session")
def pdf_hemocultivos_path(data_dir: Path) -> Path:
    """
    Informe de hemocultivos / microbiología.
    NO debería parsearse como hemograma/bioquímica/gasometría/orina.
    """
    return data_dir / "12383248W_20251108_hemocultivos.pdf"


@pytest.fixture(scope="session")
def hemato_text(pdf_hemato_path: Path) -> str:
    """Texto completo del PDF de hemato para parsers parciales."""
    return extract_text_from_pdf(str(pdf_hemato_path))
