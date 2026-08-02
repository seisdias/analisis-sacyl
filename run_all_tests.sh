#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if [[ -n "${PYTHON:-}" ]]; then
  PYTHON_BIN="$PYTHON"
elif [[ -n "${VIRTUAL_ENV:-}" && -x "$VIRTUAL_ENV/bin/python" ]]; then
  PYTHON_BIN="$VIRTUAL_ENV/bin/python"
elif [[ -x "$ROOT_DIR/.venv/bin/python" ]]; then
  PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
else
  PYTHON_BIN="python3"
fi

echo "==> Usando intérprete: $PYTHON_BIN"
echo "==> Ejecutando suite activa con cobertura"

COVERAGE_TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/analisis-sacyl-coverage.XXXXXX")"
trap 'rm -rf -- "$COVERAGE_TMP_DIR"' EXIT

export COVERAGE_FILE="$COVERAGE_TMP_DIR/.coverage"
export PYTHONDONTWRITEBYTECODE=1

"$PYTHON_BIN" -m pytest \
  -p no:cacheprovider \
  --cov-config=.coveragerc \
  --cov \
  --cov-report=term-missing \
  "$@"
