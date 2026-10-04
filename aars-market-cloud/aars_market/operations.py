from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Sequence


EXECUTION_MODE = "PAPER_ONLY"
HEALTH_EXIT_CODES = {"HEALTHY": 0, "DEGRADED": 1, "CRITICAL": 2}


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _readonly_uri(path: Path) -> str:
    return f"{path.resolve().as_uri()}?mode=ro"


def _check(check_id: str, status: str, **details: object) -> dict[str, object]:
    return {"id": check_id, "status": status, **details}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def assess_operational_health(
    db_path: str | Path,
    *,
    symbols: Sequence[str],
    timeframe: str = "1h",
    max_cycle_age: timedelta = timedelta(hours=2),
    max_candle_age: timedelta = timedelta(hours=2),
    now: datetime | None = None,
) -> dict[str, object]:
    """Inspect persisted operations without creating or modifying the database."""
    if max_cycle_age <= timedelta(0) or max_candle_age <= timedelta(0):
        raise ValueError("health age limits must be positive")
    checked_at = _utc(now or datetime.now(timezone.utc))
    path = Path(db_path).expanduser()
    checks: list[dict[str, object]] = []
    if not path.is_file():
        checks.append(_check("DATABASE", "CRITICAL", reason="database file is missing"))
        return {
            "schema_version": "mil3.operational-health.v1",
            "execution_mode": EXECUTION_MODE,
            "read_only": True,
            "checked_at": checked_at.isoformat(),
            "status": "CRITICAL",
            "checks": checks,
        }

    try:
        with sqlite3.connect(_readonly_uri(path), uri=True) as conn:
            conn.row_factory = sqlite3.Row
            integrity = conn.execute("PRAGMA quick_check").fetchone()[0]
            checks.append(
                _check(
                    "DATABASE",
                    "HEALTHY" if integrity == "ok" else "CRITICAL",
                    quick_check=integrity,
                    sqlite_version=sqlite3.sqlite_version,
                    single_writer_required=True,
                )
            )
            table_names = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
            required = {"candles", "ingestion_cycles"}
            missing = sorted(required - table_names)
            if missing:
                checks.append(
                    _check("SCHEMA", "CRITICAL", missing_tables=missing)
                )
            else:
                cycle = conn.execute(
                    """SELECT finished_at, status, summary_json
                       FROM ingestion_cycles
                       ORDER BY finished_at DESC, cycle_id DESC LIMIT 1"""
                ).fetchone()
                if cycle is None:
                    checks.append(
                        _check("INGESTION_CYCLE", "DEGRADED", reason="no completed cycle")
                    )
                else:
                    finished = _utc(datetime.fromisoformat(cycle["finished_at"]))
                    age_seconds = max(0.0, (checked_at - finished).total_seconds())
                    cycle_status = str(cycle["status"])
                    status = "HEALTHY"
                    if cycle_status == "FAILED":
                        status = "CRITICAL"
                    elif cycle_status != "SUCCESS" or age_seconds > max_cycle_age.total_seconds():
                        status = "DEGRADED"
                    checks.append(
                        _check(
                            "INGESTION_CYCLE",
                            status,
                            cycle_status=cycle_status,
                            finished_at=finished.isoformat(),
                            age_seconds=age_seconds,
                            max_age_seconds=max_cycle_age.total_seconds(),
                        )
                    )

                for symbol in (item.upper() for item in symbols):
                    row = conn.execute(
                        """SELECT MAX(open_time) AS latest
                           FROM candles WHERE symbol=? AND timeframe=?""",
                        (symbol, timeframe),
                    ).fetchone()
                    if row is None or row["latest"] is None:
                        checks.append(
                            _check(
                                "CANDLE_FRESHNESS",
                                "DEGRADED",
                                symbol=symbol,
                                timeframe=timeframe,
                                reason="no candles",
                            )
                        )
                        continue
                    latest = _utc(datetime.fromisoformat(row["latest"]))
                    age_seconds = max(0.0, (checked_at - latest).total_seconds())
                    checks.append(
                        _check(
                            "CANDLE_FRESHNESS",
                            "HEALTHY"
                            if age_seconds <= max_candle_age.total_seconds()
                            else "DEGRADED",
                            symbol=symbol,
                            timeframe=timeframe,
                            latest_at=latest.isoformat(),
                            age_seconds=age_seconds,
                            max_age_seconds=max_candle_age.total_seconds(),
                        )
                    )
    except (sqlite3.Error, ValueError, KeyError) as exc:
        checks.append(
            _check("DATABASE_ACCESS", "CRITICAL", error=f"{type(exc).__name__}: {exc}")
        )

    statuses = {str(item["status"]) for item in checks}
    overall = "CRITICAL" if "CRITICAL" in statuses else "DEGRADED" if "DEGRADED" in statuses else "HEALTHY"
    return {
        "schema_version": "mil3.operational-health.v1",
        "execution_mode": EXECUTION_MODE,
        "read_only": True,
        "checked_at": checked_at.isoformat(),
        "status": overall,
        "checks": checks,
    }


def backup_sqlite(
    db_path: str | Path,
    backup_dir: str | Path,
    *,
    retention_days: int = 30,
    now: datetime | None = None,
) -> dict[str, object]:
    """Create and verify an online SQLite backup, then prune scoped old backups."""
    if retention_days <= 0:
        raise ValueError("retention_days must be positive")
    source_path = Path(db_path).expanduser().resolve()
    if not source_path.is_file():
        raise FileNotFoundError(f"database file not found: {source_path}")
    destination_dir = Path(backup_dir).expanduser().resolve()
    destination_dir.mkdir(parents=True, exist_ok=True)
    timestamp = _utc(now or datetime.now(timezone.utc))
    filename = f"{source_path.stem}-{timestamp.strftime('%Y%m%dT%H%M%SZ')}.sqlite"
    destination = destination_dir / filename
    temporary = destination.with_suffix(".sqlite.tmp")
    if destination.exists() or temporary.exists():
        raise FileExistsError(f"backup already exists for timestamp: {destination}")

    try:
        with sqlite3.connect(_readonly_uri(source_path), uri=True) as source:
            with sqlite3.connect(temporary) as target:
                source.backup(target)
                quick_check = target.execute("PRAGMA quick_check").fetchone()[0]
                if quick_check != "ok":
                    raise sqlite3.DatabaseError(f"backup quick_check failed: {quick_check}")
        os.replace(temporary, destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise

    digest = _sha256(destination)
    cutoff = timestamp - timedelta(days=retention_days)
    removed: list[str] = []
    pattern = f"{source_path.stem}-*.sqlite"
    for candidate in sorted(destination_dir.glob(pattern)):
        if candidate == destination:
            continue
        modified = datetime.fromtimestamp(candidate.stat().st_mtime, timezone.utc)
        if modified < cutoff:
            candidate.unlink()
            removed.append(candidate.name)
    return {
        "schema_version": "mil3.backup.v1",
        "execution_mode": EXECUTION_MODE,
        "created_at": timestamp.isoformat(),
        "source": str(source_path),
        "backup": str(destination),
        "size_bytes": destination.stat().st_size,
        "sha256": digest,
        "quick_check": "ok",
        "retention_days": retention_days,
        "removed": removed,
    }


def rotate_logs(
    log_dir: str | Path,
    *,
    max_bytes: int = 10 * 1024 * 1024,
    keep: int = 7,
) -> dict[str, object]:
    """Bound launchd-managed text logs using copy-and-truncate rotation."""
    if max_bytes <= 0 or keep <= 0:
        raise ValueError("max_bytes and keep must be positive")
    directory = Path(log_dir).expanduser().resolve()
    directory.mkdir(parents=True, exist_ok=True)
    rotated: list[str] = []
    for path in sorted(directory.glob("*.log")):
        if path.stat().st_size <= max_bytes:
            continue
        oldest = path.with_name(f"{path.name}.{keep}")
        oldest.unlink(missing_ok=True)
        for index in range(keep - 1, 0, -1):
            current = path.with_name(f"{path.name}.{index}")
            if current.exists():
                current.replace(path.with_name(f"{path.name}.{index + 1}"))
        shutil.copy2(path, path.with_name(f"{path.name}.1"))
        with path.open("w", encoding="utf-8"):
            pass
        rotated.append(path.name)
    return {"log_dir": str(directory), "max_bytes": max_bytes, "keep": keep, "rotated": rotated}


def dumps(payload: dict[str, object]) -> str:
    return json.dumps(payload, sort_keys=True, allow_nan=False)
