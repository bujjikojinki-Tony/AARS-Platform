from __future__ import annotations

import copy
from datetime import timedelta
from http import HTTPStatus
from pathlib import Path

import pytest

from aars_market.isolated_config import (
    build_isolated_configuration,
    build_sandbox_event,
)
from aars_market.api import make_handler
from aars_market.isolated_runtime import (
    IsolatedRuntimeSettings,
    acquire_isolated_runtime,
    run_isolated_runtime_cycle,
    token_sha256,
)
from aars_market.models import Candle
from aars_market.runtime_ledger import (
    build_runtime_market_snapshot,
    calculate_runtime_paper_ledger,
)
from aars_market.service import DashboardService
from tests.test_mil316 import START
from tests.test_mil321 import _approved_store


RUNTIME_AT = START + timedelta(hours=300)
TOKEN = "mil323-deterministic-fencing-token"


def _ledger_ready_store(tmp_path: Path, monkeypatch):
    store, trial_id, approval_id = _approved_store(
        tmp_path,
        monkeypatch,
        approved_at=RUNTIME_AT,
        validity_hours=168,
    )
    configuration = build_isolated_configuration(
        store, trial_id, registered_at=RUNTIME_AT + timedelta(minutes=1)
    )
    configuration_id = store.archive_isolated_paper_configuration(configuration)
    activation = build_sandbox_event(
        store,
        "paper-sandbox",
        action="ACTIVATE",
        configuration_id=configuration_id,
        operator="owner",
        note="Activate deterministic paper-ledger runtime.",
        event_at=RUNTIME_AT + timedelta(minutes=2),
    )
    store.archive_isolated_paper_sandbox_event(activation)
    store.set_isolated_paper_runtime_kill_switch(
        "paper-sandbox",
        action="CLEAR",
        operator="owner",
        note="Initialize MIL-3.23 paper-ledger runtime.",
        now=RUNTIME_AT + timedelta(minutes=3),
    )
    return store, trial_id, approval_id, configuration_id


def _acquire(store, *, at=RUNTIME_AT + timedelta(minutes=4), token=TOKEN, worker="worker-a"):
    return acquire_isolated_runtime(
        store,
        "paper-sandbox",
        worker_id=worker,
        settings=IsolatedRuntimeSettings(
            lease_seconds=120, heartbeat_interval_seconds=30, max_cycles=1
        ),
        now=at,
        token_factory=lambda: token,
    )


def test_snapshot_cycle_commits_deterministic_paper_ledger_once(tmp_path: Path, monkeypatch):
    store, _, _, configuration_id = _ledger_ready_store(tmp_path, monkeypatch)
    acquired = _acquire(store)
    cycle_at = RUNTIME_AT + timedelta(minutes=4, seconds=10)
    first = run_isolated_runtime_cycle(
        store,
        acquired["session_id"],
        TOKEN,
        lease_seconds=120,
        now=cycle_at,
    )
    paper = first["paper_cycle"]
    assert paper["status"] == "COMMITTED"
    assert paper["result"]["configuration_sha256"] == acquired["configuration_sha256"]
    assert paper["result"]["aggregate"]["asset_count"] == 2
    assert paper["result"]["aggregate"]["initial_equity"] == 2000.0
    assert len(paper["result"]["per_asset"]) == 2
    assert paper["result"]["authority"]["market_source_read_only"] is True
    assert paper["result"]["authority"]["order_path_present"] is False
    cycle = store.get_isolated_paper_runtime_cycle(paper["cycle_id"])
    assert cycle["status"] == "COMMITTED"
    assert cycle["configuration_id"] == configuration_id
    assert [event["action"] for event in reversed(
        store.list_isolated_paper_runtime_cycle_events(paper["cycle_id"])
    )] == ["RESERVE", "COMMIT"]

    duplicate = run_isolated_runtime_cycle(
        store,
        acquired["session_id"],
        TOKEN,
        lease_seconds=120,
        now=cycle_at + timedelta(seconds=10),
    )["paper_cycle"]
    assert duplicate["status"] == "REUSED_COMMITTED"
    assert duplicate["result_id"] == paper["result_id"]
    assert duplicate["duplicate_application_prevented"] is True
    assert len(store.list_isolated_paper_runtime_cycles("paper-sandbox")) == 1


def test_reserved_cycle_recovers_under_new_fenced_session_after_crash(
    tmp_path: Path, monkeypatch
):
    store, *_ = _ledger_ready_store(tmp_path, monkeypatch)
    first = _acquire(store)
    reserved_at = RUNTIME_AT + timedelta(minutes=4, seconds=5)
    snapshot = build_runtime_market_snapshot(
        store, first["session_id"], observed_at=reserved_at
    )
    reservation = store.reserve_isolated_paper_runtime_cycle(
        first["session_id"],
        fencing_token_sha256=token_sha256(TOKEN),
        snapshot=snapshot,
        now=reserved_at,
    )
    assert reservation["status"] == "RESERVED_NEW"
    assert store.get_isolated_paper_runtime_cycle(snapshot["cycle_id"])["status"] == "RESERVED"

    takeover_at = RUNTIME_AT + timedelta(minutes=6, seconds=1)
    second = _acquire(
        store,
        at=takeover_at,
        token=TOKEN + "-recovery",
        worker="worker-recovery",
    )
    rebuilt = build_runtime_market_snapshot(
        store, second["session_id"], observed_at=takeover_at
    )
    recovered = store.reserve_isolated_paper_runtime_cycle(
        second["session_id"],
        fencing_token_sha256=token_sha256(TOKEN + "-recovery"),
        snapshot=rebuilt,
        now=takeover_at,
    )
    assert recovered["status"] == "RECOVERED_RESERVED"
    result = calculate_runtime_paper_ledger(store, rebuilt, calculated_at=takeover_at)
    committed = store.commit_isolated_paper_runtime_cycle(
        second["session_id"],
        fencing_token_sha256=token_sha256(TOKEN + "-recovery"),
        result=result,
        now=takeover_at,
    )
    assert committed["status"] == "COMMITTED"
    checkpoint = store.get_isolated_paper_runtime_cycle(snapshot["cycle_id"])
    assert checkpoint["attempt_count"] == 2
    assert checkpoint["owner_session_id"] == second["session_id"]
    assert [event["action"] for event in reversed(
        store.list_isolated_paper_runtime_cycle_events(snapshot["cycle_id"])
    )] == ["RESERVE", "RECOVER", "COMMIT"]


def test_source_drift_and_tampered_result_leave_checkpoint_uncommitted(
    tmp_path: Path, monkeypatch
):
    store, *_ = _ledger_ready_store(tmp_path, monkeypatch)
    acquired = _acquire(store)
    cycle_at = RUNTIME_AT + timedelta(minutes=4, seconds=5)
    snapshot = build_runtime_market_snapshot(
        store, acquired["session_id"], observed_at=cycle_at
    )
    store.reserve_isolated_paper_runtime_cycle(
        acquired["session_id"],
        fencing_token_sha256=token_sha256(TOKEN),
        snapshot=snapshot,
        now=cycle_at,
    )
    result = calculate_runtime_paper_ledger(store, snapshot, calculated_at=cycle_at)
    tampered = copy.deepcopy(result)
    tampered["aggregate"]["fees"] = 999.0
    with pytest.raises(ValueError, match="integrity failed"):
        store.commit_isolated_paper_runtime_cycle(
            acquired["session_id"],
            fencing_token_sha256=token_sha256(TOKEN),
            result=tampered,
            now=cycle_at,
        )
    assert store.get_isolated_paper_runtime_cycle(snapshot["cycle_id"])["status"] == "RESERVED"
    assert store.get_isolated_paper_ledger_result(result["result_id"]) is None

    asset = snapshot["assets"][0]
    candles = store.load_candles(
        asset["symbol"], asset["timeframe"],
        start=START, end=START + timedelta(hours=1),
    )
    original = candles[0]
    store.upsert_candles(
        [Candle(
            original.symbol, original.timeframe, original.open_time,
            original.open, original.high, original.low, original.close + 0.01,
            original.volume,
        )],
        "drift-test",
    )
    with pytest.raises(ValueError, match="source drift"):
        calculate_runtime_paper_ledger(store, snapshot, calculated_at=cycle_at)


def test_new_synchronized_boundary_chains_to_previous_committed_cycle(
    tmp_path: Path, monkeypatch
):
    store, *_ = _ledger_ready_store(tmp_path, monkeypatch)
    acquired = _acquire(store)
    cycle_at = RUNTIME_AT + timedelta(minutes=4, seconds=5)
    first = run_isolated_runtime_cycle(
        store, acquired["session_id"], TOKEN, lease_seconds=120, now=cycle_at
    )["paper_cycle"]
    for symbol in ("BTCUSDT", "ETHUSDT"):
        previous = store.load_candles(symbol, "1h", limit=1)[-1]
        next_at = previous.open_time + timedelta(hours=1)
        store.upsert_candles(
            [Candle(
                symbol, "1h", next_at, previous.close, previous.close + 0.5,
                previous.close - 0.5, previous.close + 0.1, previous.volume + 1,
            )],
            "test",
        )
    next_cycle_at = cycle_at + timedelta(hours=1, seconds=10)
    next_token = TOKEN + "-closed-boundary"
    next_session = _acquire(
        store,
        at=next_cycle_at,
        token=next_token,
        worker="worker-next-closed-boundary",
    )
    second = run_isolated_runtime_cycle(
        store,
        next_session["session_id"],
        next_token,
        lease_seconds=120,
        now=next_cycle_at,
    )["paper_cycle"]
    assert second["status"] == "COMMITTED"
    assert second["cycle_id"] != first["cycle_id"]
    checkpoint = store.get_isolated_paper_runtime_cycle(second["cycle_id"])
    assert checkpoint["previous_committed_cycle_id"] == first["cycle_id"]
    assert len(store.list_isolated_paper_runtime_cycles("paper-sandbox")) == 2


def test_checkpoint_and_ledger_apis_are_read_only_and_content_addressed(
    tmp_path: Path, monkeypatch
):
    store, *_ = _ledger_ready_store(tmp_path, monkeypatch)
    acquired = _acquire(store)
    cycle_at = RUNTIME_AT + timedelta(minutes=4, seconds=5)
    paper = run_isolated_runtime_cycle(
        store, acquired["session_id"], TOKEN, lease_seconds=120, now=cycle_at
    )["paper_cycle"]
    before_events = store.list_isolated_paper_runtime_cycle_events(paper["cycle_id"])
    handler_type = make_handler(DashboardService(store), tmp_path)
    handler = object.__new__(handler_type)

    handler.path = "/api/v1/isolated-runtime-cycles?sandbox_id=paper-sandbox"
    status, index = handler._api_payload()
    assert status == HTTPStatus.OK
    assert index["latest_cycle"]["cycle_id"] == paper["cycle_id"]
    assert index["market_source_read_only"] is True
    handler.path = f"/api/v1/isolated-runtime-cycles/{paper['cycle_id']}"
    status, checkpoint = handler._api_payload()
    assert status == HTTPStatus.OK
    assert checkpoint["status"] == "COMMITTED"
    assert checkpoint["snapshot"]["snapshot_sha256"] == paper["snapshot_sha256"]
    handler.path = f"/api/v1/isolated-runtime-cycle-events?cycle_id={paper['cycle_id']}"
    status, events = handler._api_payload()
    assert status == HTTPStatus.OK
    assert [event["action"] for event in events["events"]] == ["RESERVE", "COMMIT"]
    handler.path = f"/api/v1/isolated-paper-ledger-results/{paper['result_id']}"
    status, ledger = handler._api_payload()
    assert status == HTTPStatus.OK
    assert ledger["result"]["result_sha256"] == paper["result"]["result_sha256"]
    assert ledger["paper_orders_created"] is False
    assert ledger["order_path_present"] is False
    assert ledger["live_execution_allowed"] is False
    assert store.list_isolated_paper_runtime_cycle_events(paper["cycle_id"]) == before_events


def test_mil323_ui_exposes_snapshot_commit_idempotency_and_recovery_state():
    ui_root = Path(__file__).parents[1] / "ui"
    html = (ui_root / "index.html").read_text(encoding="utf-8")
    javascript = (ui_root / "app.js").read_text(encoding="utf-8")
    css = (ui_root / "styles.css").read_text(encoding="utf-8")
    assert "AARS // 03.25" in html
    assert 'id="runtime-cycle-checkpoint"' in html
    assert 'id="runtime-snapshot-boundary"' in html
    assert 'id="runtime-ledger-summary"' in html
    assert 'id="runtime-cycle-history"' in html
    assert "RESERVE · RECOVER · COMMIT" in html
    assert "/api/v1/isolated-runtime-cycles?sandbox_id=${encodeURIComponent(sandboxId)}" in javascript
    assert "/api/v1/isolated-runtime-cycle-events?cycle_id=${encodeURIComponent(cycleIndex.latest_cycle.cycle_id)}" in javascript
    assert "/api/v1/isolated-paper-ledger-results/${encodeURIComponent(cycleIndex.latest_cycle.result_id)}" in javascript
    assert "duplicate cycles reuse this result and cannot apply it twice" in javascript
    assert "THIS SCREEN HAS NO RUN, STOP, RECOVER OR KILL-SWITCH BUTTON" in javascript
    assert ".isolated-runtime-grid" in css
    assert 'type="button">RECOVER<' not in html
    assert 'type="button">COMMIT<' not in html
