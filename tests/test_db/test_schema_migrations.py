import os
import sqlite3
from pathlib import Path, PureWindowsPath
import stat
import time

import pytest

from db import db_schema
from db.db_manager import AnalysisDB
from db import schema_migrations as migrations


def _unversioned_current(path: Path) -> None:
    with sqlite3.connect(path) as conn:
        db_schema.create_schema(conn.cursor())
        conn.commit()


def _version(path: Path) -> int:
    with sqlite3.connect(path) as conn:
        return int(conn.execute("PRAGMA user_version").fetchone()[0])


def _tables(path: Path) -> set[str]:
    with sqlite3.connect(path) as conn:
        return {
            row[0] for row in conn.execute(
                "SELECT name FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
        }


def _legacy(path: Path, variant: str) -> None:
    _unversioned_current(path)
    with sqlite3.connect(path) as conn:
        if variant in {"core", "core_unique"}:
            for table in ("app_config", "treatment_course", "hospital_stay", "param_limit"):
                conn.execute(f"DROP TABLE {table}")
            for index in migrations.DETAIL_INDEXES:
                conn.execute(f"DROP INDEX {index}")
            if variant == "core":
                conn.execute("DROP INDEX ux_analisis_fecha_peticion")
        elif variant == "phase2_missing_all":
            for index in migrations.DETAIL_INDEXES:
                conn.execute(f"DROP INDEX {index}")
        elif variant == "phase2_missing_one":
            conn.execute("DROP INDEX ux_orina_analisis_id")
        else:
            raise AssertionError(variant)
        conn.execute(
            "INSERT INTO analisis(fecha_analisis, numero_peticion, origen) VALUES('2026-01-01','P-1','TEST')"
        )
        conn.commit()


def test_create_database_is_complete_and_versioned(tmp_path):
    path = tmp_path / "new.db"
    migrations.create_database(path)
    with sqlite3.connect(path) as conn:
        inspection = migrations.classify_schema(conn)
        assert inspection.classification == "current_versioned"
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
    assert _version(path) == migrations.CURRENT_SCHEMA_VERSION == 4


def test_creation_keeps_every_schema_change_inside_one_transaction(
    tmp_path, monkeypatch
):
    path = tmp_path / "transaction-state.db"
    real_connect = migrations.sqlite3.connect
    traced: list[tuple[str, bool]] = []

    def tracking_connect(*args, **kwargs):
        conn = real_connect(*args, **kwargs)
        conn.set_trace_callback(
            lambda sql: traced.append((sql.strip(), conn.in_transaction))
        )
        return conn

    monkeypatch.setattr(migrations.sqlite3, "connect", tracking_connect)
    migrations.create_database(path)

    begin = next((sql, active) for sql, active in traced if sql == "BEGIN IMMEDIATE")
    schema_changes = [
        (sql, active) for sql, active in traced
        if "CREATE TABLE" in sql.upper() or "CREATE INDEX" in sql.upper()
        or "CREATE UNIQUE INDEX" in sql.upper()
    ]
    version_write = next(
        (sql, active) for sql, active in traced
        if sql.upper() == "PRAGMA USER_VERSION = 4"
    )
    commit = next((sql, active) for sql, active in traced if sql == "COMMIT")
    assert begin[1] is False
    assert schema_changes and all(active for _sql, active in schema_changes)
    assert version_write[1] is True
    assert commit[1] is True


@pytest.mark.parametrize("failure_after", range(1, len(db_schema.SCHEMA_STATEMENTS) + 1))
def test_creation_failure_rolls_back_and_never_sets_version_4(tmp_path, monkeypatch, failure_after):
    path = tmp_path / f"create-failure-{failure_after}.db"
    statements = list(db_schema.SCHEMA_STATEMENTS)
    statements.insert(failure_after, "INVALID DDL")
    monkeypatch.setattr(migrations, "SCHEMA_STATEMENTS", tuple(statements))
    with pytest.raises(sqlite3.DatabaseError):
        migrations.create_database(path)
    assert _version(path) == 0
    assert _tables(path) == set()


def test_current_versioned_second_open_is_byte_for_byte_read_only(tmp_path, monkeypatch):
    path = tmp_path / "current.db"
    db = AnalysisDB(str(path))
    db.create()
    db.conn.execute("INSERT INTO app_config(key,value) VALUES('proof','unchanged')")
    db.conn.commit()
    db.close()
    before = path.read_bytes()
    before_stat = path.stat()
    real_connect = migrations.sqlite3.connect
    traced_sql: list[str] = []

    def tracking_connect(*args, **kwargs):
        conn = real_connect(*args, **kwargs)
        conn.set_trace_callback(lambda sql: traced_sql.append(sql.upper()))
        return conn

    monkeypatch.setattr(migrations.sqlite3, "connect", tracking_connect)
    monkeypatch.setattr(
        migrations, "_migrate_legacy",
        lambda _conn: (_ for _ in ()).throw(AssertionError("DDL no permitido")),
    )
    reopened = AnalysisDB(str(path))
    reopened.open()
    assert reopened.conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    assert reopened.config.config_get("proof") == "unchanged"
    reopened.close()
    after_stat = path.stat()
    assert path.read_bytes() == before
    assert after_stat.st_size == before_stat.st_size
    assert after_stat.st_mtime_ns == before_stat.st_mtime_ns
    assert list(tmp_path.glob("backups/*")) == []
    forbidden = ("CREATE ", "ALTER ", "DROP ", "PRAGMA USER_VERSION =")
    assert not any(token in sql for sql in traced_sql for token in forbidden)


def test_sqlite_rw_uri_handles_special_posix_name_and_opens_it(tmp_path):
    path = tmp_path / "espacio ñ # ?.db"
    migrations.create_database(path)
    uri = migrations.sqlite_rw_uri(path)
    assert "%20" in uri
    assert "%C3%B1" in uri
    assert "%23" in uri
    assert "%3F" in uri
    db = AnalysisDB(str(path))
    db.open()
    db.close()


def test_sqlite_rw_uri_builds_portable_encoded_windows_uri():
    path = PureWindowsPath(r"C:\Datos clínicos\base #?.db")
    assert migrations.sqlite_rw_uri(path) == (
        "file:///C:/Datos%20cl%C3%ADnicos/base%20%23%3F.db?mode=rw"
    )


def test_sqlite_rw_uri_resolves_relative_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert migrations.sqlite_rw_uri(Path("relative.db")) == (
        (tmp_path / "relative.db").as_uri() + "?mode=rw"
    )


@pytest.mark.parametrize(
    ("raw", "normalized"),
    [
        (None, None),
        (" 1 ", "1"),
        ("(1)", "1"),
        ("(( 1 ))", "1"),
        ("(1) + (2)", "(1) + (2)"),
        ("(1", "(1"),
    ],
)
def test_default_normalization_accepts_equivalent_sqlite_representation(
    raw, normalized
):
    assert migrations._normalize_default(raw) == normalized


def test_open_missing_path_does_not_create_file(tmp_path):
    path = tmp_path / "missing.db"
    with pytest.raises(FileNotFoundError):
        AnalysisDB(str(path)).open()
    assert not path.exists()


def test_create_rejects_existing_nonempty_file_without_modifying_it(tmp_path):
    path = tmp_path / "occupied.db"
    path.write_bytes(b"not a database")
    with pytest.raises(migrations.SchemaError, match="ruta nueva"):
        migrations.create_database(path)
    assert path.read_bytes() == b"not a database"


def test_adopts_exact_current_unversioned_with_verified_backup(tmp_path):
    path = tmp_path / "unversioned.db"
    _unversioned_current(path)
    with sqlite3.connect(path) as conn:
        conn.execute("INSERT INTO app_config(key,value) VALUES('kept','yes')")
        conn.commit()
    result = migrations.prepare_database(path)
    assert result.migrated
    assert result.previous_version == 0
    assert result.current_version == 4
    assert result.detected_fingerprint == "canonical"
    assert result.backup_path is not None and result.backup_path.is_file()
    assert _version(path) == 4
    with sqlite3.connect(result.backup_path) as backup:
        assert backup.execute("PRAGMA quick_check").fetchone()[0] == "ok"
        assert backup.execute("PRAGMA user_version").fetchone()[0] == 0
        assert backup.execute("SELECT value FROM app_config WHERE key='kept'").fetchone()[0] == "yes"


@pytest.mark.skipif(os.name != "posix", reason="permisos POSIX")
@pytest.mark.parametrize("preexisting_directory", [False, True])
def test_backup_and_directory_are_private_with_common_umask(
    tmp_path, preexisting_directory
):
    path = tmp_path / "private-backup.db"
    _unversioned_current(path)
    backup_dir = tmp_path / "backups"
    if preexisting_directory:
        backup_dir.mkdir(mode=0o755)
        backup_dir.chmod(0o755)

    original_umask = os.umask(0o022)
    try:
        result = migrations.prepare_database(path)
    finally:
        os.umask(original_umask)

    assert result.migrated
    assert _version(path) == migrations.CURRENT_SCHEMA_VERSION
    assert result.backup_path is not None and result.backup_path.is_file()
    assert stat.S_IMODE(backup_dir.stat().st_mode) == 0o700
    assert stat.S_IMODE(result.backup_path.stat().st_mode) == 0o600


def test_backup_failure_leaves_unversioned_database_unchanged(tmp_path, monkeypatch):
    path = tmp_path / "backup-failure.db"
    _unversioned_current(path)
    before = path.read_bytes()
    monkeypatch.setattr(
        migrations, "_backup_database",
        lambda *_args: (_ for _ in ()).throw(migrations.SchemaBackupError("backup failed")),
    )
    with pytest.raises(migrations.SchemaBackupError):
        migrations.prepare_database(path)
    assert _version(path) == 0
    assert path.read_bytes() == before


def test_incomplete_backup_file_is_removed(tmp_path):
    path = tmp_path / "source.db"
    _unversioned_current(path)

    class FailingSource:
        def backup(self, destination, **_kwargs):
            destination.execute("CREATE TABLE partial(value TEXT)")
            destination.commit()
            raise sqlite3.OperationalError("injected backup failure")

    with pytest.raises(migrations.SchemaBackupError, match="backup failure"):
        migrations._backup_database(FailingSource(), path)
    assert (tmp_path / "backups").is_dir()
    assert list((tmp_path / "backups").iterdir()) == []


def test_backup_busy_retry_has_deadline_and_removes_partial_file(
    tmp_path, monkeypatch
):
    path = tmp_path / "busy-backup-source.db"
    _unversioned_current(path)
    clock = iter((0.0, 2.0))
    monkeypatch.setattr(migrations.time, "monotonic", lambda: next(clock))

    class BusySource:
        def backup(self, _destination, *, progress, **_kwargs):
            progress(sqlite3.SQLITE_BUSY, 1, 1)

    with pytest.raises(migrations.SchemaBackupError, match="bloqueo SQLite"):
        migrations._backup_database(BusySource(), path)
    assert list((tmp_path / "backups").iterdir()) == []


def test_adoption_failure_rolls_back_and_keeps_backup(tmp_path, monkeypatch):
    path = tmp_path / "adoption-failure.db"
    _unversioned_current(path)
    real_verify = migrations._verify_canonical

    def fail_after_version(conn, expected_version):
        real_verify(conn, expected_version)
        raise RuntimeError("injected adoption failure")

    monkeypatch.setattr(migrations, "_verify_canonical", fail_after_version)
    with pytest.raises(migrations.SchemaMigrationError, match="injected adoption failure"):
        migrations.prepare_database(path)
    assert _version(path) == 0
    assert len(list((tmp_path / "backups").glob("*.sqlite3"))) == 1


@pytest.mark.parametrize(
    "variant, fingerprint",
    [
        ("core", "legacy_normalized_core"),
        ("core_unique", "legacy_normalized_unique_analysis"),
        ("phase2_missing_all", "legacy_phase2_missing_detail_uniques"),
        ("phase2_missing_one", "legacy_phase2_missing_detail_uniques"),
    ],
)
def test_supported_legacy_variants_migrate_and_preserve_content(tmp_path, variant, fingerprint):
    path = tmp_path / f"{variant}.db"
    _legacy(path, variant)
    result = migrations.prepare_database(path)
    assert result.detected_fingerprint == fingerprint
    assert result.backup_path is not None and result.backup_path.exists()
    with sqlite3.connect(path) as conn:
        assert migrations.classify_schema(conn).classification == "current_versioned"
        assert conn.execute("SELECT numero_peticion FROM analisis").fetchone()[0] == "P-1"


@pytest.mark.parametrize("table", ["analisis", "hematologia", "bioquimica", "gasometria", "orina"])
def test_legacy_duplicates_are_rejected_without_changes_or_backup(tmp_path, table):
    path = tmp_path / f"duplicate-{table}.db"
    _legacy(path, "core")
    with sqlite3.connect(path) as conn:
        if table == "analisis":
            conn.execute(
                "INSERT INTO analisis(fecha_analisis,numero_peticion) VALUES('2026-01-01','P-1')"
            )
        else:
            conn.execute(f"INSERT INTO {table}(analisis_id) VALUES(1)")
            conn.execute(f"INSERT INTO {table}(analisis_id) VALUES(1)")
        conn.commit()
    before = path.read_bytes()
    with pytest.raises(migrations.UnsupportedSchemaError, match="duplicados"):
        migrations.prepare_database(path)
    assert path.read_bytes() == before
    assert not (tmp_path / "backups").exists()


@pytest.mark.parametrize("version", [1, 2, 3, 5])
def test_unrecognised_formal_and_future_versions_are_rejected(tmp_path, version):
    path = tmp_path / f"version-{version}.db"
    _unversioned_current(path)
    with sqlite3.connect(path) as conn:
        conn.execute(f"PRAGMA user_version = {version}")
    error = migrations.FutureSchemaError if version > 4 else migrations.UnsupportedSchemaError
    with pytest.raises(error):
        migrations.prepare_database(path)
    assert _version(path) == version
    assert not (tmp_path / "backups").exists()


def test_version_4_with_wrong_shape_is_rejected(tmp_path):
    path = tmp_path / "wrong-v4.db"
    migrations.create_database(path)
    with sqlite3.connect(path) as conn:
        conn.execute("DROP INDEX ux_orina_analisis_id")
    with pytest.raises(migrations.UnsupportedSchemaError):
        migrations.prepare_database(path)
    assert _version(path) == 4
    assert not (tmp_path / "backups").exists()


def test_partial_index_with_canonical_name_is_not_accepted(tmp_path):
    path = tmp_path / "partial-index.db"
    _unversioned_current(path)
    with sqlite3.connect(path) as conn:
        conn.execute("DROP INDEX ux_orina_analisis_id")
        conn.execute(
            "CREATE UNIQUE INDEX ux_orina_analisis_id ON orina(analisis_id) "
            "WHERE analisis_id > 0"
        )
    with pytest.raises(migrations.UnsupportedSchemaError):
        migrations.prepare_database(path)
    assert _version(path) == 0
    assert not (tmp_path / "backups").exists()


@pytest.mark.parametrize("kind", ["empty", "foreign", "partial", "extra", "denormalized"])
def test_unsupported_shapes_are_rejected_without_backup(tmp_path, kind):
    path = tmp_path / f"{kind}.db"
    with sqlite3.connect(path) as conn:
        if kind == "foreign":
            conn.execute("CREATE TABLE foreign_data(id INTEGER PRIMARY KEY)")
        elif kind == "partial":
            conn.execute("CREATE TABLE analisis(id INTEGER PRIMARY KEY)")
        elif kind == "extra":
            db_schema.create_schema(conn.cursor())
            conn.execute("CREATE TABLE unexpected(value TEXT)")
        elif kind == "denormalized":
            conn.execute("CREATE TABLE paciente(id INTEGER PRIMARY KEY)")
            conn.execute(
                "CREATE TABLE hematologia(id INTEGER PRIMARY KEY, fecha_analisis TEXT, numero_peticion TEXT)"
            )
        conn.commit()
    with pytest.raises(migrations.UnsupportedSchemaError):
        migrations.prepare_database(path)
    assert _version(path) == 0
    assert not (tmp_path / "backups").exists()


def test_corrupt_database_with_sqlite_header_is_rejected(tmp_path):
    path = tmp_path / "corrupt.db"
    path.write_bytes(b"SQLite format 3\x00" + b"broken" * 100)
    with pytest.raises((migrations.SchemaIntegrityError, sqlite3.DatabaseError)):
        migrations.prepare_database(path)
    assert not (tmp_path / "backups").exists()


def test_foreign_key_inconsistency_is_rejected_before_backup(tmp_path):
    path = tmp_path / "orphan.db"
    _unversioned_current(path)
    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA foreign_keys = OFF")
        conn.execute("INSERT INTO hematologia(analisis_id) VALUES(999)")
        conn.commit()
    with pytest.raises(migrations.SchemaIntegrityError, match="clave foránea"):
        migrations.prepare_database(path)
    assert _version(path) == 0
    assert not (tmp_path / "backups").exists()


def test_migration_failure_rolls_back_all_ddl_and_keeps_backup(tmp_path, monkeypatch):
    path = tmp_path / "migration-failure.db"
    _legacy(path, "core")
    before_tables = _tables(path)

    def partial_then_fail(conn):
        conn.execute("CREATE TABLE app_config(key TEXT PRIMARY KEY, value TEXT)")
        raise RuntimeError("injected DDL failure")

    monkeypatch.setattr(migrations, "_migrate_legacy", partial_then_fail)
    with pytest.raises(migrations.SchemaMigrationError, match="injected DDL failure"):
        migrations.prepare_database(path)
    assert _version(path) == 0
    assert _tables(path) == before_tables
    assert len(list((tmp_path / "backups").glob("*.sqlite3"))) == 1
    with sqlite3.connect(path) as conn:
        assert conn.execute("PRAGMA quick_check").fetchone()[0] == "ok"


@pytest.mark.parametrize("failure_after", range(len(db_schema.SCHEMA_STATEMENTS) + 1))
def test_failure_at_each_migration_ddl_position_rolls_back(tmp_path, monkeypatch, failure_after):
    path = tmp_path / f"migration-step-{failure_after}.db"
    _legacy(path, "core")
    before = path.read_bytes()
    statements = list(db_schema.SCHEMA_STATEMENTS)
    statements.insert(failure_after, "INVALID DDL")
    monkeypatch.setattr(migrations, "SCHEMA_STATEMENTS", tuple(statements))
    with pytest.raises(migrations.SchemaMigrationError):
        migrations.prepare_database(path)
    assert _version(path) == 0
    assert path.read_bytes() == before
    assert len(list((tmp_path / "backups").glob("*.sqlite3"))) == 1


def test_backup_api_includes_committed_wal_content(tmp_path):
    path = tmp_path / "wal.db"
    _unversioned_current(path)
    writer = sqlite3.connect(path)
    try:
        assert writer.execute("PRAGMA journal_mode=WAL").fetchone()[0].lower() == "wal"
        writer.execute("INSERT INTO app_config(key,value) VALUES('wal-proof','committed')")
        writer.commit()
        result = migrations.prepare_database(path)
    finally:
        writer.close()
    assert result.backup_path is not None
    with sqlite3.connect(result.backup_path) as backup:
        assert backup.execute(
            "SELECT value FROM app_config WHERE key='wal-proof'"
        ).fetchone()[0] == "committed"


def test_migration_lock_timeout_is_controlled_and_keeps_version_zero(tmp_path):
    path = tmp_path / "locked.db"
    _unversioned_current(path)
    locker = sqlite3.connect(path)
    try:
        locker.execute("BEGIN IMMEDIATE")
        started = time.monotonic()
        with pytest.raises(migrations.SchemaMigrationError, match="locked"):
            migrations.prepare_database(path)
        elapsed = time.monotonic() - started
    finally:
        locker.rollback()
        locker.close()
    assert elapsed < 3
    assert _version(path) == 0
    backups = list((tmp_path / "backups").glob("*.sqlite3"))
    assert len(backups) == 1


def test_exclusive_lock_rejects_validation_without_backup_or_version_change(tmp_path):
    path = tmp_path / "exclusive-lock.db"
    _unversioned_current(path)
    locker = sqlite3.connect(path)
    try:
        locker.execute("BEGIN EXCLUSIVE")
        started = time.monotonic()
        with pytest.raises(migrations.SchemaIntegrityError, match="locked"):
            migrations.prepare_database(path)
        elapsed = time.monotonic() - started
    finally:
        locker.rollback()
        locker.close()
    assert elapsed < 3
    assert _version(path) == 0
    assert not (tmp_path / "backups").exists()
