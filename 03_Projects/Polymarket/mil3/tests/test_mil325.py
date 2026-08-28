from __future__ import annotations

import copy
import plistlib
import subprocess
import sys
from datetime import timedelta
from http import HTTPStatus
from pathlib import Path

import pytest

from aars_market.forward_ops import (
    build_cycle_account_deltas,
    build_forward_bot_operations_view,
    calculate_continuous_burn_in,
    run_forward_bot_wake,
    verify_forward_bot_operations_view,
)
from aars_market.api import make_handler
from aars_market.isolated_runtime import (
    IsolatedRuntimeSettings,
    acquire_isolated_runtime,
    token_sha256,
)
from aars_market.macos_deployment import (
    LABEL_PREFIX,
    MacOSDeploymentConfig,
    forward_bot_launch_agent_payload,
    launch_agent_payloads,
    render_forward_bot_launch_agent,
)
from aars_market.models import Candle
from aars_market.runtime_ledger import build_runtime_market_snapshot
from aars_market.service import DashboardService
from tests.test_mil323 import RUNTIME_AT, TOKEN, _ledger_ready_store


def _append_next_closed_candidate(store) -> None:
    for symbol in ("BTCUSDT", "ETHUSDT"):
        previous = store.load_candles(symbol, "1h", limit=1)[-1]
        store.upsert_candles(
            [Candle(
                symbol,
                "1h",
                previous.open_time + timedelta(hours=1),
                previous.close,
                previous.close + 0.5,
                previous.close - 0.5,
                previous.close + 0.1,
                previous.volume + 1,
            )],
            "mil325-test",
        )


def test_closed_bar_wake_commits_once_waits_and_emits_account_deltas(
    tmp_path: Path, monkeypatch
):
    store, *_ = _ledger_ready_store(tmp_path, monkeypatch)
    first_at = RUNTIME_AT + timedelta(minutes=4)
    first = run_forward_bot_wake(
        store,
        "paper-sandbox",
        now=first_at,
        token_factory=lambda: TOKEN,
    )
    assert first["status"] == "COMMITTED"
    assert first["cycle_executed"] is True
    assert first["operations"]["cycle_delta"]["status"] == "GENESIS"
    assert first["operations"]["trigger"]["new_closed_bar"] is False

    duplicate = run_forward_bot_wake(
        store,
        "paper-sandbox",
        now=first_at + timedelta(minutes=1),
    )
    assert duplicate["status"] == "WAITING_NO_NEW_CLOSED_BAR"
    assert duplicate["cycle_executed"] is False
    assert len(store.list_isolated_paper_runtime_cycles("paper-sandbox")) == 1

    _append_next_closed_candidate(store)
    still_open = run_forward_bot_wake(
        store,
        "paper-sandbox",
        now=first_at + timedelta(minutes=2),
    )
    assert still_open["status"] == "WAITING_NO_NEW_CLOSED_BAR"

    second_at = first_at + timedelta(hours=1, minutes=1)
    second = run_forward_bot_wake(
        store,
        "paper-sandbox",
        now=second_at,
        token_factory=lambda: TOKEN + "-mil325-next",
    )
    assert second["status"] == "COMMITTED"
    delta = second["operations"]["cycle_delta"]
    assert delta["status"] == "DELTA"
    assert len(delta["bots"]) == 4
    assert all(item["lineage"] == "DELTA" for item in delta["bots"])
    assert all(len(item["per_asset"]) == 2 for item in delta["bots"])
    assert all(
        asset["new_simulated_fills"] >= 0
        for bot in delta["bots"]
        for asset in bot["per_asset"]
    )
    assert verify_forward_bot_operations_view(second["operations"]) is True

    cycles = store.list_isolated_paper_runtime_cycles("paper-sandbox")
    current_result = store.get_isolated_paper_ledger_result(cycles[0]["result_id"])
    previous_result = store.get_isolated_paper_ledger_result(cycles[1]["result_id"])
    tampered_previous = copy.deepcopy(previous_result)
    tampered_previous["aggregate"]["fees"] = 999.0
    unavailable = build_cycle_account_deltas(current_result, tampered_previous)
    assert unavailable["status"] == "UNAVAILABLE"
    assert unavailable["bots"] == []

    with store.connect() as conn:
        conn.execute(
            "UPDATE isolated_paper_runtime_cycles SET previous_committed_cycle_id=NULL WHERE cycle_id=?",
            (cycles[0]["cycle_id"],),
        )
    broken = build_forward_bot_operations_view(
        store, "paper-sandbox", now=second_at
    )
    assert any(item["code"] == "CYCLE_LINEAGE_BROKEN" for item in broken["alerts"])
    assert broken["status"] == "BLOCKED"


def test_concurrent_wake_is_skipped_by_existing_runtime_lease(tmp_path: Path, monkeypatch):
    store, *_ = _ledger_ready_store(tmp_path, monkeypatch)
    at = RUNTIME_AT + timedelta(minutes=4)
    acquire_isolated_runtime(
        store,
        "paper-sandbox",
        worker_id="existing-worker",
        settings=IsolatedRuntimeSettings(
            lease_seconds=120, heartbeat_interval_seconds=30, max_cycles=1
        ),
        now=at,
        token_factory=lambda: TOKEN,
    )
    wake = run_forward_bot_wake(
        store,
        "paper-sandbox",
        now=at + timedelta(seconds=5),
        token_factory=lambda: TOKEN + "-racing-wake",
    )
    assert wake["status"] == "SKIPPED_CONCURRENT_WAKE"
    assert wake["cycle_executed"] is False
    assert len(store.list_isolated_paper_runtime_sessions("paper-sandbox")) == 1


def test_stale_reserved_checkpoint_creates_actionable_critical_alert(
    tmp_path: Path, monkeypatch
):
    store, *_ = _ledger_ready_store(tmp_path, monkeypatch)
    at = RUNTIME_AT + timedelta(minutes=4)
    acquired = acquire_isolated_runtime(
        store,
        "paper-sandbox",
        worker_id="crash-worker",
        settings=IsolatedRuntimeSettings(
            lease_seconds=120, heartbeat_interval_seconds=30, max_cycles=1
        ),
        now=at,
        token_factory=lambda: TOKEN,
    )
    snapshot = build_runtime_market_snapshot(
        store, acquired["session_id"], observed_at=at
    )
    store.reserve_isolated_paper_runtime_cycle(
        acquired["session_id"],
        fencing_token_sha256=token_sha256(TOKEN),
        snapshot=snapshot,
        now=at,
    )
    report = build_forward_bot_operations_view(
        store,
        "paper-sandbox",
        now=at + timedelta(minutes=10),
        reserved_timeout=timedelta(minutes=5),
    )
    alert = next(
        item for item in report["alerts"]
        if item["code"] == "CHECKPOINT_RESERVED_TOO_LONG"
    )
    assert report["status"] == "BLOCKED"
    assert alert["severity"] == "CRITICAL"
    assert "bounded recovery wake" in alert["recommended_response"]

    recovered = run_forward_bot_wake(
        store,
        "paper-sandbox",
        now=at + timedelta(minutes=10),
        token_factory=lambda: TOKEN + "-mil325-recovery",
    )
    assert recovered["status"] == "COMMITTED"
    cycle = store.list_isolated_paper_runtime_cycles("paper-sandbox")[0]
    assert cycle["attempt_count"] == 2
    assert [event["action"] for event in reversed(
        store.list_isolated_paper_runtime_cycle_events(cycle["cycle_id"])
    )] == ["RESERVE", "RECOVER", "COMMIT"]


def test_burn_in_tracks_seven_fourteen_days_and_resets_after_large_gap():
    interval = timedelta(hours=1)
    seven_days = [RUNTIME_AT + index * interval for index in range(7 * 24)]
    minimum = calculate_continuous_burn_in(
        seven_days,
        interval=interval,
        minimum_days=7,
        target_days=14,
    )
    assert minimum["status"] == "MINIMUM_7D_REACHED"
    assert minimum["minimum_ready"] is True
    assert minimum["target_ready"] is False

    fourteen_days = [RUNTIME_AT + index * interval for index in range(14 * 24)]
    target = calculate_continuous_burn_in(
        fourteen_days,
        interval=interval,
        minimum_days=7,
        target_days=14,
    )
    assert target["status"] == "TARGET_14D_REACHED"
    assert target["target_ready"] is True

    gapped = fourteen_days[:24] + [item + timedelta(days=3) for item in fourteen_days[24:48]]
    reset = calculate_continuous_burn_in(
        gapped,
        interval=interval,
        minimum_days=7,
        target_days=14,
    )
    assert reset["status"] == "BURN_IN_RUNNING"
    assert reset["continuous_cycles"] == 24


def test_forward_launch_agent_is_deferred_separate_and_one_shot(tmp_path: Path):
    project_root = Path(__file__).parents[1]
    config = MacOSDeploymentConfig(
        project_root=project_root,
        python_executable=Path(sys.executable),
        runtime_root=tmp_path / "runtime",
    )
    assert "forward-bots" not in launch_agent_payloads(config)
    payload = forward_bot_launch_agent_payload(
        config,
        sandbox_id="paper-sandbox",
        interval_seconds=60,
        lease_seconds=120,
    )
    assert payload["Label"] == f"{LABEL_PREFIX}.forward-bots"
    assert payload["RunAtLoad"] is False
    assert payload["KeepAlive"] is False
    assert payload["StartInterval"] == 60
    assert "run_forward_bot_operations.py" in " ".join(payload["ProgramArguments"])
    assert "WAKE" in payload["ProgramArguments"]

    path = render_forward_bot_launch_agent(
        config,
        tmp_path / "staged-agents",
        sandbox_id="paper-sandbox",
    )
    assert path.stat().st_mode & 0o777 == 0o600
    assert plistlib.loads(path.read_bytes())["KeepAlive"] is False
    with pytest.raises(FileExistsError):
        render_forward_bot_launch_agent(config, tmp_path / "staged-agents")


def test_forward_operations_cli_status_remains_paper_only(tmp_path: Path):
    command = [
        sys.executable,
        str(Path(__file__).parents[1] / "run_forward_bot_operations.py"),
        "--db",
        str(tmp_path / "empty.sqlite"),
        "--action",
        "STATUS",
        "--sandbox-id",
        "paper-sandbox",
    ]
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    assert '"execution_mode": "PAPER_ONLY"' in completed.stdout
    assert '"status": "BLOCKED"' in completed.stdout
    assert '"live_execution_allowed": false' in completed.stdout


def test_forward_operations_api_and_ui_are_read_only(tmp_path: Path, monkeypatch):
    store, *_ = _ledger_ready_store(tmp_path, monkeypatch)
    before_cycles = store.list_isolated_paper_runtime_cycles("paper-sandbox")
    handler_type = make_handler(DashboardService(store), tmp_path)
    handler = object.__new__(handler_type)
    handler.path = "/api/v1/forward-bot-operations?sandbox_id=paper-sandbox"
    status, payload = handler._api_payload()
    assert status == HTTPStatus.OK
    assert payload["schema_version"] == "mil3.forward-bot-operations.v1"
    assert payload["authority"]["read_only_view"] is True
    assert payload["authority"]["browser_control_allowed"] is False
    assert payload["authority"]["order_path_present"] is False
    assert payload["authority"]["live_execution_allowed"] is False
    assert store.list_isolated_paper_runtime_cycles("paper-sandbox") == before_cycles

    ui_root = Path(__file__).parents[1] / "ui"
    html = (ui_root / "index.html").read_text(encoding="utf-8")
    javascript = (ui_root / "app.js").read_text(encoding="utf-8")
    css = (ui_root / "styles.css").read_text(encoding="utf-8")
    assert "AARS // 03.25" in html
    assert 'id="forward-bot-trigger"' in html
    assert 'id="forward-bot-delta"' in html
    assert 'id="forward-bot-burn-in"' in html
    assert 'id="forward-bot-alerts"' in html
    assert "/api/v1/forward-bot-operations?sandbox_id=${encodeURIComponent(sandboxId)}" in javascript
    assert "Only synchronized fully closed candles" in javascript
    assert "a gap over two intervals resets" in javascript
    assert ".runtime-alert-section" in css
    assert 'type="button">WAKE<' not in html
    assert 'type="button">START BOT<' not in html
