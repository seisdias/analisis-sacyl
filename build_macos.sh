#!/usr/bin/env bash
set -euo pipefail

APP_NAME="salud_v1"
ENTRY="app/web_main.py"

# 0) venv limpio
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip wheel

# 1) deps (API + webview)
pip install -r requirements.txt
pip install -r requirements-webview.txt
pip install pyinstaller

# 2) limpiar builds anteriores
rm -rf build dist

# 3) build .app
# IMPORTANTE macOS: --add-data usa ":" como separador (origen:destino)
pyinstaller \
  --noconfirm \
  --clean \
  --windowed \
  --name "${APP_NAME}" \
  --add-data "web:web" \
  --hidden-import "api.server" \
  --hidden-import "api.routers.core" \
  --hidden-import "api.routers.sessions" \
  --hidden-import "api.routers.imports" \
  --hidden-import "api.routers.charts" \
  --hidden-import "api.routers.patient" \
  --hidden-import "api.routers.timeline" \
  --hidden-import "api.routers.limits" \
  "${ENTRY}"

echo ""
echo "✅ Build terminado: dist/${APP_NAME}.app"
echo "🔎 Verificando presencia de web..."
test -f "dist/${APP_NAME}.app/Contents/Resources/web/shell.html" && echo "OK: shell.html" || (echo "ERROR: falta web/shell.html" && exit 2)
test -f "dist/${APP_NAME}.app/Contents/Resources/web/dashboard.html" && echo "OK: dashboard.html" || (echo "ERROR: falta web/dashboard.html" && exit 2)
test -f "dist/${APP_NAME}.app/Contents/Resources/web/assets/app.js" && echo "OK: assets/app.js" || (echo "ERROR: falta web/assets/app.js" && exit 2)

echo "✅ Web incluida dentro del .app"