from __future__ import annotations

import hashlib
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_build_and_tools_profiles_are_separated():
    build = _text("requirements-build.txt").lower()
    tools = _text("requirements-tools.txt").lower()
    runtime = _text("requirements.txt").lower()
    desktop = _text("requirements-webview.txt").lower()
    assert "pyinstaller>=6,<7" in build
    assert "pyinstaller-hooks-contrib" in build
    assert "requirements.txt" in build and "requirements-webview.txt" in build
    assert "reportlab>=4.2,<5" in tools
    assert "reportlab" not in build + runtime + desktop
    assert all(name not in build + tools for name in ("numpy", "matplotlib", "tksheet"))


def test_echarts_is_local_versioned_and_verified():
    html = _text("web/dashboard.html")
    asset = ROOT / "web/assets/vendor/echarts-5.6.0.min.js"
    readme = _text("web/assets/vendor/README.md")
    license_text = _text("web/assets/vendor/LICENSE-echarts.txt")
    assert "cdn.jsdelivr.net" not in html and "unpkg.com" not in html
    assert './assets/vendor/echarts-5.6.0.min.js' in html
    assert asset.stat().st_size > 900_000
    asset_bytes = asset.read_bytes()
    assert b"Apache Software Foundation" in asset_bytes[:2_000]
    assert b"5.6.0" in asset_bytes
    assert "Apache License" in license_text and "Version 2.0" in license_text
    assert "5.6.0" in readme and "raw.githubusercontent.com/apache/echarts/5.6.0" in readme
    documented = re.search(r"SHA-256.*`([0-9a-f]{64})`", readme).group(1)
    assert hashlib.sha256(asset_bytes).hexdigest() == documented


def test_echarts_asset_is_exempt_from_git_text_normalization():
    attributes = _text(".gitattributes").splitlines()
    assert "web/assets/vendor/echarts-5.6.0.min.js -text" in attributes
    assert not any(line.startswith("web/") for line in attributes if "echarts-5.6.0.min.js" not in line)


def test_pyinstaller_spec_is_onedir_and_scoped():
    spec = _text("AnalisisSACYL.spec")
    assert 'ROOT / "app" / "web_main.py"' in spec
    assert 'name="AnalisisSACYL"' in spec
    assert 'ROOT / "web"' in spec and '"web"' in spec
    assert (ROOT / "web/assets/vendor/echarts-5.6.0.min.js").is_file()
    assert 'collect_submodules("lab_pdf")' in spec
    assert 'collect_submodules("fastapi")' in spec
    assert 'collect_submodules("uvicorn")' in spec
    assert 'collect_submodules("webview")' in spec
    assert "COLLECT(" in spec and "onefile" not in spec.lower()
    assert "console=False" in spec
    datas = spec.split("datas=[", 1)[1].split("hiddenimports=", 1)[0].lower()
    assert 'root / "web"' in datas
    assert not any(name in datas for name in ("tests", "data", "uploads", "backups", "build", "dist", "htmlcov", ".db", ".sqlite", ".pdf"))


def test_windows_script_validates_before_cleaning_and_never_installs():
    script = _text("scripts/build_windows.sh")
    lower = script.lower()
    assert "mingw" in lower and "windows_nt" in lower
    assert "sys.version_info[:2] == (3, 12)" in script
    assert "import PyInstaller" in script and "import webview" in script
    assert "AnalisisSACYL.spec" in script and "echarts-5.6.0.min.js" in script
    assert lower.index("falta echarts") < lower.index("rm -rf -- build dist")
    assert "pip install" not in lower and "pip upgrade" not in lower
    assert "python -m PyInstaller --noconfirm --clean AnalisisSACYL.spec" in script
    assert "dist/AnalisisSACYL/AnalisisSACYL.exe" in script
    assert 'timeout 30s "$EXE" --smoke-test' in script
    assert "*.spec" not in script


def test_windows_workflow_is_focused_and_checks_artifact():
    workflow = _text(".github/workflows/build-windows.yml")
    assert "workflow_dispatch:" in workflow and "push:" in workflow and "paths:" in workflow
    assert "runs-on: windows-latest" in workflow
    assert 'python-version: "3.12"' in workflow
    for profile in ("requirements.txt", "requirements-dev.txt", "requirements-webview.txt", "requirements-build.txt"):
        assert profile in workflow
    for focused_test in (
        "tests/test_js_bridge_runtime.py",
        "tests/test_offline_build_packaging.py",
        "tests/test_requirements_profiles.py",
        "tests/test_runtime_paths.py",
        "tests/test_web_main_runtime.py",
    ):
        assert workflow.count(focused_test) >= 2
    assert "run_all_tests.sh" not in workflow
    assert "bash scripts/build_windows.sh" in workflow
    assert "AnalisisSACYL.exe --smoke-test" in workflow
    for marker in ("pdf", "db", "sqlite", "uploads", "backups", "tests"):
        assert marker in workflow.lower()
    assert "actions/upload-artifact@v4" in workflow and "dist/AnalisisSACYL/" in workflow


def test_gitignore_keeps_required_files_and_ignores_local_outputs():
    lines = set(_text(".gitignore").splitlines())
    required = {
        ".venv/", "__pycache__/", "*.py[cod]", ".pytest_cache/", "htmlcov/",
        ".coverage", "build/", "dist/", "*.db", "*.sqlite", "*.sqlite3",
        "*-wal", "*-shm", "backups/", "**/backups/", "data/", "app/data/",
        "uploads/", "**/uploads/",
    }
    assert required <= lines
    assert "*.spec" not in lines
    assert {"!.coveragerc", "!AnalisisSACYL.spec", "!tests/data/*.pdf", "!web/assets/vendor/*"} <= lines
    assert not (ROOT / ".coverage").exists()
    assert not (ROOT / "listado.txt").exists()


def test_environment_documentation_covers_operational_contract():
    doc = _text("docs/ENVIRONMENT_AND_BUILD.md")
    for phrase in (
        "Python 3.12", "requirements.txt", "requirements-dev.txt",
        "requirements-webview.txt", "requirements-build.txt", "requirements-tools.txt",
        "bash run_all_tests.sh", "python -m app.web_main --browser",
        "python -m app.web_main --desktop", "python -m app.web_main --smoke-test",
        "ANALISIS_SACYL_DATA_DIR", "SALUD_V1_DATA_DIR", "ANALISIS_SACYL_PORT",
        "ECharts 5.6.0", "windows-latest", "Python 3.14", "backup",
    ):
        assert phrase in doc
    assert "firma" in doc and "instalador" in doc and "macOS" in doc
