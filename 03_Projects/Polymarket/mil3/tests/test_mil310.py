from __future__ import annotations

import hashlib
import os
import plistlib
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from aars_market.macos_deployment import (
    LABEL_PREFIX,
    MacOSDeploymentConfig,
    install_launch_agents,
    uninstall_launch_agents,
)
from aars_market.models import Candle
from aars_market.operations import assess_operational_health, backup_sqlite, rotate_logs
from aars_market.storage import MarketStore


NOW = datetime(2026, 8, 24, 12, tzinfo=timezone.utc)
SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")


def _seed_store(path: Path, *, cycle_status: str = "SUCCESS") -> MarketStore:
    store = MarketStore(path)
    store.init_db()
    candles = [
        Candle(symbol, "1h", NOW - timedelta(hours=1), 100, 101, 99, 100, 1000)
        for symbol in SYMBOLS
    ]
    store.upsert_candles(candles, "test")
    store.record_ingestion_cycle(
        {
            "execution_mode": "PAPER_ONLY",
            "started_at": (NOW - timedelta(minutes=2)).isoformat(),
            "finished_at": (NOW - timedelta(minutes=1)).isoformat(),
            "status": cycle_status,
            "resources": [],
        }
    )
    return store


def test_health_check_is_read_only_and_reports_healthy_store(tmp_path: Path):
    db = tmp_path / "market.sqlite"
    _seed_store(db)
    before = hashlib.sha256(db.read_bytes()).hexdigest()

    payload = assess_operational_health(db, symbols=SYMBOLS, now=NOW)

    assert payload["status"] == "HEALTHY"
    assert payload["execution_mode"] == "PAPER_ONLY"
    assert payload["read_only"] is True
    assert hashlib.sha256(db.read_bytes()).hexdigest() == before
    assert len([item for item in payload["checks"] if item["id"] == "CANDLE_FRESHNESS"]) == 3


def test_health_check_missing_database_does_not_create_it(tmp_path: Path):
    db = tmp_path / "missing.sqlite"

    payload = assess_operational_health(db, symbols=SYMBOLS, now=NOW)

    assert payload["status"] == "CRITICAL"
    assert payload["checks"][0]["reason"] == "database file is missing"
    assert not db.exists()


def test_health_check_degrades_on_partial_cycle_and_stale_candle(tmp_path: Path):
    db = tmp_path / "market.sqlite"
    _seed_store(db, cycle_status="PARTIAL")

    payload = assess_operational_health(
        db,
        symbols=SYMBOLS,
        now=NOW + timedelta(hours=4),
        max_cycle_age=timedelta(hours=2),
        max_candle_age=timedelta(hours=2),
    )

    assert payload["status"] == "DEGRADED"
    assert any(
        item["id"] == "INGESTION_CYCLE" and item["status"] == "DEGRADED"
        for item in payload["checks"]
    )
    assert all(
        item["status"] == "DEGRADED"
        for item in payload["checks"]
        if item["id"] == "CANDLE_FRESHNESS"
    )


def test_online_backup_is_consistent_and_prunes_only_scoped_old_files(tmp_path: Path):
    db = tmp_path / "market.sqlite"
    store = _seed_store(db)
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    old = backup_dir / "market-20260101T000000Z.sqlite"
    old.write_bytes(b"old")
    os.utime(old, (NOW.timestamp() - 40 * 86400, NOW.timestamp() - 40 * 86400))
    unrelated = backup_dir / "other.sqlite"
    unrelated.write_bytes(b"preserve")

    payload = backup_sqlite(db, backup_dir, retention_days=30, now=NOW)
    backup = Path(str(payload["backup"]))

    assert payload["quick_check"] == "ok"
    assert payload["removed"] == [old.name]
    assert unrelated.exists()
    assert hashlib.sha256(backup.read_bytes()).hexdigest() == payload["sha256"]
    store.upsert_candles(
        [Candle("SOLUSDT", "1h", NOW, 101, 102, 100, 101, 1000)], "after-backup"
    )
    with sqlite3.connect(backup) as conn:
        count = conn.execute("SELECT COUNT(*) FROM candles").fetchone()[0]
    assert count == 3


def test_log_rotation_bounds_active_log_and_retains_history(tmp_path: Path):
    log = tmp_path / "scheduler.log"
    log.write_text("abcdefgh", encoding="utf-8")

    first = rotate_logs(tmp_path, max_bytes=4, keep=2)
    assert first["rotated"] == ["scheduler.log"]
    assert log.read_text(encoding="utf-8") == ""
    assert (tmp_path / "scheduler.log.1").read_text(encoding="utf-8") == "abcdefgh"

    log.write_text("ijklmnop", encoding="utf-8")
    rotate_logs(tmp_path, max_bytes=4, keep=2)
    assert (tmp_path / "scheduler.log.1").read_text(encoding="utf-8") == "ijklmnop"
    assert (tmp_path / "scheduler.log.2").read_text(encoding="utf-8") == "abcdefgh"


def test_launch_agents_use_absolute_paths_localhost_and_preserve_data_on_uninstall(
    tmp_path: Path,
):
    project_root = Path(__file__).parents[1]
    runtime_root = tmp_path / "runtime"
    agents_dir = tmp_path / "LaunchAgents"
    config = MacOSDeploymentConfig(
        project_root=project_root,
        python_executable=Path(sys.executable),
        runtime_root=runtime_root,
    )

    installed = install_launch_agents(config, agents_dir, load=False)

    assert Path(str(installed["database"])).is_file()
    plist_paths = [Path(item) for item in installed["plists"]]
    assert len(plist_paths) == 4
    payloads = {path.stem: plistlib.loads(path.read_bytes()) for path in plist_paths}
    api = payloads[f"{LABEL_PREFIX}.api"]
    scheduler = payloads[f"{LABEL_PREFIX}.scheduler"]
    assert "127.0.0.1" in api["ProgramArguments"]
    assert "0.0.0.0" not in api["ProgramArguments"]
    assert api["KeepAlive"] is True and scheduler["KeepAlive"] is True
    assert all(Path(path).stat().st_mode & 0o777 == 0o600 for path in plist_paths)

    result = uninstall_launch_agents(agents_dir, unload=False)

    assert result["runtime_data_preserved"] is True
    assert config.db_path.exists()
    assert not any(agents_dir.glob(f"{LABEL_PREFIX}.*.plist"))
