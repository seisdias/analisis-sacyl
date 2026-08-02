#!/usr/bin/env bash
set -euo pipefail

fail() {
  echo "[ERROR] $*" >&2
  exit 1
}

case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*) ;;
  *) fail "Este build requiere Windows con Git Bash." ;;
esac

[ "${OS:-}" = "Windows_NT" ] || fail "No se detectó un entorno Windows válido."

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

command -v python >/dev/null 2>&1 || fail "Python no está disponible en PATH."
python -c 'import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)' \
  || fail "Se requiere Python 3.12."
python -c 'import sys; raise SystemExit(0 if sys.executable and sys.prefix else 1)' \
  || fail "El intérprete o entorno virtual no es válido."
python -c 'import PyInstaller' >/dev/null 2>&1 \
  || fail "Falta PyInstaller; instala requirements-build.txt."
python -c 'import webview' >/dev/null 2>&1 \
  || fail "Falta pywebview; instala requirements-webview.txt."

[ -f "AnalisisSACYL.spec" ] || fail "Falta AnalisisSACYL.spec."
[ -s "web/assets/vendor/echarts-5.6.0.min.js" ] || fail "Falta ECharts 5.6.0 offline."
[ -f "app/web_main.py" ] || fail "Falta app/web_main.py."
[ -f "requirements.txt" ] || fail "Falta requirements.txt."
[ -d "web" ] && [ -d "lab_pdf" ] || fail "La estructura del repositorio está incompleta."

echo "[INFO] Validaciones correctas; limpiando build/ y dist/."
rm -rf -- build dist

echo "[INFO] Construyendo AnalisisSACYL (onedir)."
python -m PyInstaller --noconfirm --clean AnalisisSACYL.spec

EXE="dist/AnalisisSACYL/AnalisisSACYL.exe"
[ -f "$EXE" ] || fail "No se generó $EXE."
command -v timeout >/dev/null 2>&1 || fail "Falta el comando timeout de Git Bash."

echo "[INFO] Ejecutando smoke test (30 s)."
timeout 30s "$EXE" --smoke-test || fail "El smoke test del ejecutable falló o agotó el plazo."
echo "[OK] Build validado: $EXE"
