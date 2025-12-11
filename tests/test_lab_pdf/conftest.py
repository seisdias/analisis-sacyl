from pathlib import Path

import pytest

from lab_pdf.pdf_utils import extract_text_from_pdf


# Carpeta de tests y carpeta de datos
TESTS_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = TESTS_DIR / "data"


@pytest.fixture(scope="session")
def hemato_pdf_path() -> Path:
    """
    Ruta al PDF de hemograma/bioquímica/gasometría completo (informe estándar).
    """
    return DATA_DIR / "12383248W_20251111.pdf"


@pytest.fixture(scope="session")
def hemocultivos_pdf_path() -> Path:
    """
    Ruta al PDF de hemocultivos, que NO debe parsearse como análisis estándar.
    """
    return DATA_DIR / "12383248W_20251108_hemocultivos.pdf"


@pytest.fixture(scope="session")
def hemato_text(hemato_pdf_path: Path) -> str:
    """
    Texto completo del PDF de hemato, para parsers que trabajan con texto.
    """
    return extract_text_from_pdf(str(hemato_pdf_path))
