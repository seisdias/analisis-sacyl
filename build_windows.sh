#!/usr/bin/env bash
set -e

echo "======================================"
echo " AnalisisSACYL - Build Windows Portable"
echo "======================================"

# Guardamos el directorio actual
ROOT_DIR="$(pwd)"

# 1. Comprobar existencia del venv
if [ ! -d ".venv" ]; then
  echo "[ERROR] No existe el entorno virtual .venv"
  echo "        Créalo con:"
  echo "        py -3.12 -m venv .venv"
  echo "        python -m pip install -r requirements.txt"
  exit 1
fi

echo "[OK] Entorno virtual .venv encontrado"

# 2. Activar entorno virtual (Git Bash)
echo "[INFO] Activando entorno virtual..."
source .venv/Scripts/activate

echo "[INFO] Python activo:"
python -V

# 3. Limpieza previa de builds
echo "[INFO] Limpiando builds anteriores..."
rm -rf build dist *.spec

# 4. Ejecutar PyInstaller
echo "[INFO] Ejecutando PyInstaller..."
python -m PyInstaller \
  --noconsole \
  --name AnalisisSACYL \
  --paths . \
  --add-data "web;web" \
  --add-data "lab_pdf;lab_pdf" \
  app/web_main.py

# 5. Build completado
echo "--------------------------------------"
echo "[OK] Build completado correctamente"
echo "[OK] Ejecutable disponible en:"
echo "     dist/AnalisisSACYL/AnalisisSACYL.exe"
echo "--------------------------------------"

# 6. Desactivar entorno virtual
echo "[INFO] Desactivando entorno virtual..."
deactivate

# Volver al directorio original (por seguridad)
cd "$ROOT_DIR"

echo "======================================"
echo " Build finalizado"
echo "======================================"
