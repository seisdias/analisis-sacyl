#!/usr/bin/env bash
set -euo pipefail

# Ir a la raíz del proyecto (directorio donde está este script)
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

# Permite sobreescribir el intérprete (por ejemplo PYTHON=python3 ./run_all_tests.sh)
PYTHON="${PYTHON:-python}"

echo "==> Usando intérprete: $PYTHON"

echo "==> Limpiando datos de cobertura anteriores..."
$PYTHON -m coverage erase || true

echo "==> Ejecutando tests con pytest + pytest-cov..."
$PYTHON -m pytest tests \
  --cov=db_manager \
  --cov=lab_pdf \
  --cov=analisis_view \
  --cov=ranges \
  --cov=ranges_config \
  --cov-report=term-missing \
  --cov-fail-under=80


echo "==> Generando informe HTML de cobertura..."
$PYTHON -m coverage html

echo
echo "✅ Tests OK y cobertura suficiente."
echo "   Informe HTML disponible en: htmlcov/index.html"
