from __future__ import annotations

import sys
from pathlib import Path

from app import paths


def test_primary_data_environment_has_priority(tmp_path, monkeypatch):
    primary = tmp_path / "principal con espacios # ? ñ"
    monkeypatch.setenv("ANALISIS_SACYL_DATA_DIR", str(primary))
    monkeypatch.setenv("SALUD_V1_DATA_DIR", str(tmp_path / "alias"))
    assert paths.data_root() == primary.resolve()
    assert not primary.exists()


def test_legacy_data_environment_is_compatible_alias(tmp_path, monkeypatch):
    alias = tmp_path / "salud-v1"
    monkeypatch.delenv("ANALISIS_SACYL_DATA_DIR", raising=False)
    monkeypatch.setenv("SALUD_V1_DATA_DIR", str(alias))
    assert paths.data_root() == alias.resolve()


def test_home_fallback_is_stable_and_independent_of_cwd(tmp_path, monkeypatch):
    home, cwd_one, cwd_two = tmp_path / "home", tmp_path / "cwd-one", tmp_path / "cwd-two"
    cwd_one.mkdir()
    cwd_two.mkdir()
    monkeypatch.delenv("ANALISIS_SACYL_DATA_DIR", raising=False)
    monkeypatch.delenv("SALUD_V1_DATA_DIR", raising=False)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    monkeypatch.chdir(cwd_one)
    first = paths.data_root()
    monkeypatch.chdir(cwd_two)
    assert paths.data_root() == first == (home / ".analisis-sacyl").resolve()
    assert not first.exists()


def test_frozen_resources_are_not_a_data_destination(tmp_path, monkeypatch):
    bundle, writable = tmp_path / "frozen bundle", tmp_path / "writable"
    monkeypatch.setattr(sys, "_MEIPASS", str(bundle), raising=False)
    monkeypatch.setenv("ANALISIS_SACYL_DATA_DIR", str(writable))
    assert paths.resource_root() == bundle.resolve()
    assert paths.web_root() == bundle.resolve() / "web"
    assert paths.default_database_path() == writable.resolve() / "analisis.db"
    assert bundle not in paths.default_database_path().parents


def test_runtime_directories_are_separate_and_created_lazily(tmp_path, monkeypatch):
    root = tmp_path / "datos con espacios ñ # ?"
    monkeypatch.setenv("ANALISIS_SACYL_DATA_DIR", str(root))
    assert not root.exists()
    pdfs = paths.pdf_uploads_dir()
    databases = paths.database_uploads_dir()
    temporary = paths.runtime_temp_dir()
    assert pdfs == root.resolve() / "uploads" / "pdfs"
    assert databases == root.resolve() / "uploads" / "databases"
    assert temporary == root.resolve() / "tmp"
    assert len({pdfs, databases, temporary}) == 3
    assert all(path.is_dir() for path in (pdfs, databases, temporary))
