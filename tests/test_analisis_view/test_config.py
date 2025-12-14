# tests/test_analisis_view/test_config.py

from __future__ import annotations

from analisis_view.config import (
    HEMA_FIELDS,
    BIOQ_FIELDS,
    ORINA_FIELDS,
    HEMA_VISIBLE_FIELDS,
    BIOQ_VISIBLE_FIELDS,
    ORINA_VISIBLE_FIELDS,
    HEMA_HEADERS,
    BIOQ_HEADERS,
    ORINA_HEADERS,
)


def test_hema_fields_basics():
    # Comprobamos que algunos campos clave están presentes
    assert "id" in HEMA_FIELDS
    assert "fecha_analisis" in HEMA_FIELDS
    assert "hemoglobina" in HEMA_FIELDS
    assert "plaquetas" in HEMA_FIELDS

    # El orden debe empezar por id, fecha_analisis, numero_peticion, origen
    assert HEMA_FIELDS[0] == "id"
    assert HEMA_FIELDS[1] == "fecha_analisis"
    assert HEMA_FIELDS[2] == "numero_peticion"
    assert HEMA_FIELDS[3] == "origen"


def test_hema_visible_fields_exclude_only_id():
    # 'id' no debe estar en los campos visibles, 'origen' sí.
    assert "id" not in HEMA_VISIBLE_FIELDS
    assert "origen" in HEMA_VISIBLE_FIELDS

    # Algunos parámetros clave deben estar visibles
    assert "hemoglobina" in HEMA_VISIBLE_FIELDS
    assert "plaquetas" in HEMA_VISIBLE_FIELDS
    # La fecha también debe estar visible
    assert "fecha_analisis" in HEMA_VISIBLE_FIELDS
    assert "numero_peticion" in HEMA_VISIBLE_FIELDS


def test_bioq_visible_fields_exclude_only_id():
    assert "id" in BIOQ_FIELDS
    assert "id" not in BIOQ_VISIBLE_FIELDS

    # 'numero_peticion' sigue siendo visible
    if "numero_peticion" in BIOQ_FIELDS:
        assert "numero_peticion" in BIOQ_VISIBLE_FIELDS

    # Algunos parámetros clave deben estar visibles
    assert "creatinina" in BIOQ_VISIBLE_FIELDS
    assert "colesterol_total" in BIOQ_VISIBLE_FIELDS
    assert "fecha_analisis" in BIOQ_VISIBLE_FIELDS


def test_orina_visible_fields_exclude_only_id():
    assert "id" in ORINA_FIELDS
    assert "id" not in ORINA_VISIBLE_FIELDS

    # La fecha debe seguir visible
    assert "fecha_analisis" in ORINA_VISIBLE_FIELDS

    # Algunos parámetros clave
    assert "densidad" in ORINA_VISIBLE_FIELDS
    assert "proteinas" in ORINA_VISIBLE_FIELDS
    assert "numero_peticion" in ORINA_VISIBLE_FIELDS


def test_headers_have_legible_names_for_some_fields():
    # HEMATOLOGÍA
    assert HEMA_HEADERS["hemoglobina"] == "Hemoglobina (g/dL)"
    assert HEMA_HEADERS["plaquetas"].startswith("Plaquetas")
    assert HEMA_HEADERS["fecha_analisis"] == "Fecha"

    # BIOQUÍMICA
    assert BIOQ_HEADERS["creatinina"] == "Creatinina"
    assert "Colesterol" in BIOQ_HEADERS["colesterol_total"]
    assert BIOQ_HEADERS["fecha_analisis"] == "Fecha"

    # ORINA
    assert ORINA_HEADERS["ph"] == "pH"
    assert ORINA_HEADERS["densidad"] == "Densidad"
    assert ORINA_HEADERS["fecha_analisis"] == "Fecha"
