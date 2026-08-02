# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules


ROOT = Path(SPECPATH).resolve()

# Only the read-only web tree is added as data. Consequently tests and PDF
# fixtures, data, databases, uploads, backups, build, dist, tools, and htmlcov
# are outside the bundle by construction. lab_pdf is Python code, not data.
hiddenimports = (
    collect_submodules("fastapi")
    + collect_submodules("uvicorn")
    + collect_submodules("webview")
    + collect_submodules("lab_pdf")
)

a = Analysis(
    [str(ROOT / "app" / "web_main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[(str(ROOT / "web"), "web")],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "pytest",
        "reportlab",
        "matplotlib",
        "numpy",
        "tksheet",
        "scripts",
        "tests",
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="AnalisisSACYL",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="AnalisisSACYL",
)
