from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import os
from pathlib import Path, PurePath, PureWindowsPath
import sqlite3
import time
from typing import Callable
from uuid import uuid4

from .db_schema import CURRENT_SCHEMA_VERSION, SCHEMA_STATEMENTS

_SCHEMA_LOCK_TIMEOUT_SECONDS = 1.0
_BACKUP_RETRY_SLEEP_SECONDS = 0.05


class SchemaError(RuntimeError):
    """Base class for schema validation and migration failures."""


class UnsupportedSchemaError(SchemaError):
    pass


class FutureSchemaError(SchemaError):
    pass


class SchemaIntegrityError(SchemaError):
    pass


class SchemaMigrationError(SchemaError):
    pass


class SchemaBackupError(SchemaError):
    pass


@dataclass(frozen=True)
class Column:
    name: str
    declared_type: str
    not_null: bool
    default: str | None
    pk_position: int


@dataclass(frozen=True)
class ForeignKey:
    columns: tuple[str, ...]
    target_table: str
    target_columns: tuple[str, ...]
    on_delete: str


@dataclass(frozen=True)
class TableShape:
    columns: tuple[Column, ...]
    foreign_keys: tuple[ForeignKey, ...] = ()


@dataclass(frozen=True)
class IndexShape:
    table: str
    unique: bool
    columns: tuple[str, ...]
    partial: bool = False


@dataclass(frozen=True)
class SchemaSnapshot:
    user_version: int
    tables: dict[str, TableShape]
    indexes: dict[str, IndexShape]


@dataclass(frozen=True)
class SchemaInspection:
    classification: str
    fingerprint: str
    snapshot: SchemaSnapshot


@dataclass(frozen=True)
class PreparationResult:
    migrated: bool
    previous_version: int
    current_version: int
    backup_path: Path | None
    detected_fingerprint: str


def _col(name: str, declared_type: str, *, not_null: bool = False,
         default: str | None = None, pk: int = 0) -> Column:
    return Column(name, declared_type, not_null, default, pk)


ID = _col("id", "INTEGER", pk=1)
ANALISIS = TableShape((
    ID, _col("fecha_analisis", "TEXT", not_null=True),
    _col("numero_peticion", "TEXT"), _col("origen", "TEXT"),
))
PACIENTE = TableShape((
    ID, _col("nombre", "TEXT"), _col("apellidos", "TEXT"),
    _col("fecha_nacimiento", "TEXT"), _col("sexo", "TEXT"),
    _col("numero_historia", "TEXT"),
))


def _detail(columns: tuple[Column, ...]) -> TableShape:
    return TableShape(
        (ID, _col("analisis_id", "INTEGER", not_null=True), *columns),
        (ForeignKey(("analisis_id",), "analisis", ("id",), "CASCADE"),),
    )


HEMATOLOGIA = _detail(tuple(_col(name, "REAL") for name in (
    "leucocitos", "neutrofilos_pct", "linfocitos_pct", "monocitos_pct",
    "eosinofilos_pct", "basofilos_pct", "neutrofilos_abs", "linfocitos_abs",
    "monocitos_abs", "eosinofilos_abs", "basofilos_abs", "hematies",
    "hemoglobina", "hematocrito", "vcm", "hcm", "chcm", "rdw",
    "plaquetas", "vpm",
)))
BIOQUIMICA = _detail(tuple(_col(name, "REAL") for name in (
    "glucosa", "urea", "creatinina", "sodio", "potasio", "cloro", "calcio",
    "fosforo", "colesterol_total", "colesterol_hdl", "colesterol_ldl",
    "colesterol_no_hdl", "trigliceridos", "indice_riesgo", "hierro",
    "ferritina", "vitamina_b12",
)))
GASOMETRIA = _detail(tuple(_col(name, "REAL") for name in (
    "gaso_ph", "gaso_pco2", "gaso_po2", "gaso_tco2", "gaso_so2_calc",
    "gaso_so2", "gaso_p50", "gaso_bicarbonato", "gaso_sbc", "gaso_eb",
    "gaso_beecf", "gaso_lactato",
)))
ORINA = _detail((
    _col("ph", "REAL"), _col("densidad", "REAL"), _col("glucosa", "TEXT"),
    _col("proteinas", "TEXT"), _col("cuerpos_cetonicos", "TEXT"),
    _col("sangre", "TEXT"), _col("nitritos", "TEXT"),
    _col("leucocitos_ests", "TEXT"), _col("bilirrubina", "TEXT"),
    _col("urobilinogeno", "TEXT"), _col("sodio_ur", "REAL"),
    _col("creatinina_ur", "REAL"), _col("indice_albumina_creatinina", "REAL"),
    _col("albumina_ur", "REAL"), _col("categoria_albuminuria", "TEXT"),
))

CORE_TABLES = {
    "analisis": ANALISIS, "paciente": PACIENTE, "hematologia": HEMATOLOGIA,
    "bioquimica": BIOQUIMICA, "gasometria": GASOMETRIA, "orina": ORINA,
}
PHASE2_TABLES = {
    "app_config": TableShape((_col("key", "TEXT", pk=1), _col("value", "TEXT"))),
    "treatment_course": TableShape((
        ID, _col("name", "TEXT"), _col("start_date", "TEXT"),
        _col("end_date", "TEXT"), _col("standard_days", "INTEGER"),
        _col("notes", "TEXT"),
    )),
    "hospital_stay": TableShape((
        ID, _col("admission_date", "TEXT"), _col("discharge_date", "TEXT"),
        _col("notes", "TEXT"),
    )),
    "param_limit": TableShape((
        ID, _col("param_key", "TEXT", not_null=True),
        _col("value", "REAL", not_null=True), _col("label", "TEXT"),
        _col("enabled", "INTEGER", not_null=True, default="1"),
    )),
}
CANONICAL_TABLES = {**CORE_TABLES, **PHASE2_TABLES}
ANALISIS_INDEX = {
    "ux_analisis_fecha_peticion": IndexShape(
        "analisis", True, ("fecha_analisis", "numero_peticion")
    )
}
DETAIL_INDEXES = {
    f"ux_{table}_analisis_id": IndexShape(table, True, ("analisis_id",))
    for table in ("hematologia", "bioquimica", "gasometria", "orina")
}
PHASE2_INDEXES = {
    "idx_param_limit_key": IndexShape("param_limit", False, ("param_key",))
}
CANONICAL_INDEXES = {**ANALISIS_INDEX, **DETAIL_INDEXES, **PHASE2_INDEXES}


def sqlite_rw_uri(path: str | PurePath) -> str:
    """Build a safely encoded SQLite URI for an existing database."""
    if isinstance(path, PureWindowsPath):
        absolute = path
    else:
        candidate = Path(path).expanduser()
        absolute = candidate if candidate.is_absolute() else candidate.resolve()
    return f"{absolute.as_uri()}?mode=rw"


def _open_existing(path: Path) -> sqlite3.Connection:
    if not path.is_file():
        raise UnsupportedSchemaError("La base SQLite no existe o no es un archivo regular")
    return sqlite3.connect(
        sqlite_rw_uri(path.resolve()),
        uri=True,
        check_same_thread=False,
        timeout=_SCHEMA_LOCK_TIMEOUT_SECONDS,
    )


def _normalize_default(value: object) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    while normalized.startswith("(") and normalized.endswith(")"):
        depth = 0
        encloses_whole_value = True
        for position, character in enumerate(normalized):
            if character == "(":
                depth += 1
            elif character == ")":
                depth -= 1
                if depth == 0 and position != len(normalized) - 1:
                    encloses_whole_value = False
                    break
        if not encloses_whole_value or depth != 0:
            break
        normalized = normalized[1:-1].strip()
    return normalized


def inspect_schema(conn: sqlite3.Connection) -> SchemaSnapshot:
    user_version = int(conn.execute("PRAGMA user_version").fetchone()[0])
    names = tuple(row[0] for row in conn.execute(
        "SELECT name FROM sqlite_schema WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ))
    tables: dict[str, TableShape] = {}
    indexes: dict[str, IndexShape] = {}
    for name in names:
        quoted = name.replace('"', '""')
        columns = tuple(
            Column(
                str(row[1]),
                " ".join(str(row[2]).upper().split()),
                bool(row[3]),
                _normalize_default(row[4]),
                int(row[5]),
            )
            for row in conn.execute(f'PRAGMA table_info("{quoted}")')
        )
        fk_rows = conn.execute(f'PRAGMA foreign_key_list("{quoted}")').fetchall()
        grouped: dict[int, list[sqlite3.Row | tuple]] = {}
        for row in fk_rows:
            grouped.setdefault(int(row[0]), []).append(row)
        foreign_keys = []
        for key_rows in grouped.values():
            ordered = sorted(key_rows, key=lambda row: int(row[1]))
            foreign_keys.append(ForeignKey(
                tuple(str(row[3]) for row in ordered), str(ordered[0][2]),
                tuple(str(row[4]) for row in ordered), str(ordered[0][6]).upper(),
            ))
        tables[name] = TableShape(columns, tuple(sorted(
            foreign_keys, key=lambda fk: (fk.columns, fk.target_table)
        )))
        for row in conn.execute(f'PRAGMA index_list("{quoted}")'):
            index_name = str(row[1])
            if index_name.startswith("sqlite_"):
                continue
            iq = index_name.replace('"', '""')
            index_columns = tuple(
                str(info[2]) for info in conn.execute(f'PRAGMA index_info("{iq}")')
            )
            indexes[index_name] = IndexShape(
                name, bool(row[2]), index_columns, bool(row[4])
            )
    return SchemaSnapshot(user_version, tables, indexes)


def _shape_name(snapshot: SchemaSnapshot) -> str:
    if not snapshot.tables:
        return "empty"
    if snapshot.tables == CANONICAL_TABLES and snapshot.indexes == CANONICAL_INDEXES:
        return "canonical"
    if snapshot.tables == CORE_TABLES and snapshot.indexes == {}:
        return "legacy_normalized_core"
    if snapshot.tables == CORE_TABLES and snapshot.indexes == ANALISIS_INDEX:
        return "legacy_normalized_unique_analysis"
    expected_phase2_base = {**ANALISIS_INDEX, **PHASE2_INDEXES}
    if snapshot.tables == CANONICAL_TABLES:
        allowed = set(DETAIL_INDEXES)
        present = set(snapshot.indexes) - set(expected_phase2_base)
        if (all(snapshot.indexes.get(k) == v for k, v in expected_phase2_base.items())
                and present < allowed
                and all(snapshot.indexes.get(k) == DETAIL_INDEXES[k] for k in present)
                and set(snapshot.indexes) == set(expected_phase2_base) | present):
            return "legacy_phase2_missing_detail_uniques"
    known = set(CANONICAL_TABLES)
    if set(snapshot.tables) & known:
        detail_names = ("hematologia", "bioquimica", "gasometria", "orina")
        if any(
            name in snapshot.tables
            and any(col.name in {"fecha_extraccion", "fecha_analisis"}
                    for col in snapshot.tables[name].columns)
            and all(col.name != "analisis_id" for col in snapshot.tables[name].columns)
            for name in detail_names
        ):
            return "unsupported_denormalized"
        return "inconsistent"
    return "foreign"


def classify_schema(conn: sqlite3.Connection) -> SchemaInspection:
    snapshot = inspect_schema(conn)
    shape = _shape_name(snapshot)
    version = snapshot.user_version
    if version > CURRENT_SCHEMA_VERSION:
        return SchemaInspection("future", shape, snapshot)
    if version in (1, 2, 3):
        return SchemaInspection("unsupported_legacy", shape, snapshot)
    if version == CURRENT_SCHEMA_VERSION:
        classification = "current_versioned" if shape == "canonical" else "inconsistent"
        return SchemaInspection(classification, shape, snapshot)
    if version != 0:
        return SchemaInspection("unsupported_legacy", shape, snapshot)
    mapping = {
        "empty": "new_empty",
        "foreign": "foreign",
        "canonical": "current_unversioned",
        "legacy_normalized_core": "legacy_normalized_supported",
        "legacy_normalized_unique_analysis": "legacy_normalized_supported",
        "legacy_phase2_missing_detail_uniques": "legacy_normalized_supported",
        "unsupported_denormalized": "unsupported_legacy",
        "inconsistent": "inconsistent",
    }
    return SchemaInspection(mapping[shape], shape, snapshot)


def _check_integrity(conn: sqlite3.Connection) -> None:
    try:
        rows = conn.execute("PRAGMA quick_check").fetchall()
        foreign_key_errors = conn.execute("PRAGMA foreign_key_check").fetchall()
    except sqlite3.DatabaseError as exc:
        raise SchemaIntegrityError(f"No se pudo comprobar la coherencia SQLite: {exc}") from exc
    if [str(row[0]).lower() for row in rows] != ["ok"]:
        raise SchemaIntegrityError("La comprobación de coherencia SQLite ha fallado")
    if foreign_key_errors:
        raise SchemaIntegrityError("La base contiene relaciones de clave foránea incoherentes")


def _verify_canonical(conn: sqlite3.Connection, expected_version: int) -> None:
    snapshot = inspect_schema(conn)
    if (snapshot.user_version != expected_version
            or snapshot.tables != CANONICAL_TABLES
            or snapshot.indexes != CANONICAL_INDEXES):
        raise SchemaIntegrityError("El esquema resultante no coincide con el esquema canónico")


def create_database(path: str | Path) -> None:
    db_path = Path(path)
    if db_path.exists():
        if not db_path.is_file() or db_path.stat().st_size != 0:
            raise SchemaError("La creación requiere una ruta nueva o un archivo vacío reservado")
    else:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        with db_path.open("xb"):
            pass
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("BEGIN IMMEDIATE")
        for statement in SCHEMA_STATEMENTS:
            conn.execute(statement)
        snapshot = inspect_schema(conn)
        if snapshot.tables != CANONICAL_TABLES or snapshot.indexes != CANONICAL_INDEXES:
            raise SchemaIntegrityError("No se pudo crear el esquema canónico completo")
        conn.execute(f"PRAGMA user_version = {CURRENT_SCHEMA_VERSION}")
        _verify_canonical(conn, CURRENT_SCHEMA_VERSION)
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        conn.close()


def _backup_database(source: sqlite3.Connection, db_path: Path) -> Path:
    backup_dir = db_path.parent / "backups"
    backup_path: Path | None = None
    try:
        backup_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        if os.name == "posix":
            os.chmod(backup_dir, 0o700)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
        backup_path = backup_dir / (
            f"{db_path.name}.pre-migration-v0-to-v{CURRENT_SCHEMA_VERSION}-"
            f"{stamp}-{uuid4().hex}.sqlite3"
        )
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
        descriptor = os.open(backup_path, flags, 0o600)
        os.close(descriptor)
        destination = sqlite3.connect(str(backup_path))
        try:
            deadline = time.monotonic() + _SCHEMA_LOCK_TIMEOUT_SECONDS

            def stop_if_locked_too_long(
                status: int, _remaining: int, _total: int
            ) -> None:
                if (
                    status in {sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED}
                    and time.monotonic() >= deadline
                ):
                    raise SchemaBackupError(
                        "El backup no pudo adquirir un bloqueo SQLite a tiempo"
                    )

            source.backup(
                destination,
                pages=256,
                progress=stop_if_locked_too_long,
                sleep=_BACKUP_RETRY_SLEEP_SECONDS,
            )
        finally:
            destination.close()
        with backup_path.open("rb") as handle:
            if handle.read(16) != b"SQLite format 3\x00":
                raise SchemaBackupError("El backup no tiene una cabecera SQLite válida")
        verified = _open_existing(backup_path)
        try:
            _check_integrity(verified)
        finally:
            verified.close()
        return backup_path
    except Exception as exc:
        if backup_path is not None:
            try:
                backup_path.unlink(missing_ok=True)
            except OSError:
                pass
        if isinstance(exc, SchemaBackupError):
            raise
        raise SchemaBackupError(f"No se pudo crear o verificar el backup: {exc}") from exc


def _ensure_no_duplicates(conn: sqlite3.Connection) -> None:
    checks = [
        ("analisis", "fecha_analisis, numero_peticion", "numero_peticion IS NOT NULL"),
        ("hematologia", "analisis_id", "1"),
        ("bioquimica", "analisis_id", "1"),
        ("gasometria", "analisis_id", "1"),
        ("orina", "analisis_id", "1"),
    ]
    for table, columns, condition in checks:
        row = conn.execute(
            f"SELECT 1 FROM {table} WHERE {condition} GROUP BY {columns} "
            "HAVING COUNT(*) > 1 LIMIT 1"
        ).fetchone()
        if row:
            raise UnsupportedSchemaError(
                f"La tabla {table} contiene duplicados incompatibles con el esquema actual"
            )


def _migrate_legacy(conn: sqlite3.Connection) -> None:
    for statement in SCHEMA_STATEMENTS:
        conn.execute(statement)


# Future formal migrations are registered here, e.g. 4: migrate_4_to_5.
MIGRATIONS: dict[int, Callable[[sqlite3.Connection], None]] = {}


def prepare_database(path: str | Path, *, check_integrity: bool = True) -> PreparationResult:
    db_path = Path(path).expanduser().resolve()
    conn = _open_existing(db_path)
    try:
        if check_integrity:
            _check_integrity(conn)
        inspection = classify_schema(conn)
        if inspection.classification == "future":
            raise FutureSchemaError(
                f"La base usa una versión futura ({inspection.snapshot.user_version})"
            )
        if inspection.classification == "current_versioned":
            return PreparationResult(False, CURRENT_SCHEMA_VERSION,
                                     CURRENT_SCHEMA_VERSION, None, inspection.fingerprint)
        if inspection.classification not in {
            "current_unversioned", "legacy_normalized_supported"
        }:
            messages = {
                "new_empty": "Una SQLite sin tablas no puede abrirse como base existente",
                "foreign": "La base SQLite pertenece a otra aplicación",
                "inconsistent": "El esquema SACYL está incompleto o es incompatible",
                "unsupported_legacy": "La versión o el esquema histórico no está soportado",
            }
            raise UnsupportedSchemaError(messages.get(
                inspection.classification, "Esquema SQLite no soportado"
            ))
        if inspection.classification == "legacy_normalized_supported":
            _ensure_no_duplicates(conn)
        backup_path = _backup_database(conn, db_path)
        try:
            conn.execute("PRAGMA busy_timeout = 1000")
            conn.execute("BEGIN IMMEDIATE")
            _check_integrity(conn)
            reinspection = classify_schema(conn)
            if (reinspection.classification != inspection.classification
                    or reinspection.fingerprint != inspection.fingerprint):
                raise SchemaMigrationError("El esquema cambió durante la preparación")
            if inspection.classification == "legacy_normalized_supported":
                _ensure_no_duplicates(conn)
                _migrate_legacy(conn)
            snapshot = inspect_schema(conn)
            if snapshot.tables != CANONICAL_TABLES or snapshot.indexes != CANONICAL_INDEXES:
                raise SchemaIntegrityError("La migración no produjo el esquema canónico")
            conn.execute(f"PRAGMA user_version = {CURRENT_SCHEMA_VERSION}")
            _verify_canonical(conn, CURRENT_SCHEMA_VERSION)
            conn.commit()
        except Exception as exc:
            try:
                conn.rollback()
            except Exception:
                pass
            if isinstance(exc, SchemaError):
                raise
            raise SchemaMigrationError(f"Falló la migración del esquema: {exc}") from exc
        return PreparationResult(True, 0, CURRENT_SCHEMA_VERSION,
                                 backup_path, inspection.fingerprint)
    finally:
        conn.close()
