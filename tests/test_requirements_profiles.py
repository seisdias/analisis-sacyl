from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _requirements(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8").lower()


def test_direct_dependencies_are_in_their_runtime_profiles():
    runtime = _requirements("requirements.txt")
    development = _requirements("requirements-dev.txt")
    webview = _requirements("requirements-webview.txt")
    for dependency in ("fastapi", "pydantic", "pypdf", "python-multipart", "uvicorn"):
        assert dependency in runtime
    assert "pytest" not in runtime and "pywebview" not in runtime
    assert "pytest" in development and "httpx>=0.27,<0.29" in development
    assert "pywebview" in webview and "pytest" not in webview
    forbidden = ("numpy", "matplotlib", "tksheet", "reportlab", "pyinstaller", "httpx2")
    assert not any(name in runtime + webview for name in forbidden)
