from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from pathlib import Path

import pytest

from aars_market.isolated_config import build_sandbox_event
from aars_market.api import make_handler
from aars_market.isolated_runtime import (
    IsolatedRuntimeSettings,
    acquire_isolated_runtime,
    run_isolated_paper_runtime,
    run_isolated_runtime_cycle,
)
from aars_market.service import DashboardService
from tests.test_mil316 import START
from tests.test_mil321 import _approved_store, _registered_store


TOKEN = "deterministic-runtime-fencing-token"


def _active_store(tmp_path: Path, monkeypatch):
    store, trial_id, approval_id, configuration_id, payload = _registered_store(
        tmp_path, monkeypatch
    )
    store.set_isolated_paper_runtime_kill_switch(
        "paper-sandbox",
        action="CLEAR",
        operator="owner",
        note="Initialize local PAPER_ONLY runtime control.",
        now=START + timedelta(minutes=2),
    )
    activation = build_sandbox_event(
        store,
        "paper-sandbox",
        action="ACTIVATE",
        configuration_id=configuration_id,
        operator="owner",
        note="Activate for governed runtime test.",
        event_at=START + timedelta(hours=1),
    )
    store.archive_isolated_paper_sandbox_event(activation)
    return store, trial_id, approval_id, configuration_id, payload


def _acquire(store, *, at=START + timedelta(hours=2), token=TOKEN, worker="worker-a"):
    return acquire_isolated_runtime(
        store,
        "paper-sandbox",
        worker_id=worker,
        settings=IsolatedRuntimeSettings(
            lease_seconds=30, heartbeat_interval_seconds=10, max_cycles=1
        ),
        now=at,
        token_factory=lambda: token,
    )


def test_kill_switch_defaults_fail_safe_and_fenced_lease_renews(
    tmp_path: Path, monkeypatch
):
    store, _, _, configuration_id, _ = _registered_store(tmp_path, monkeypatch)
    assert store.isolated_paper_runtime_kill_switch("paper-sandbox")[
        "effective_state"
    ] == "ARMED"
    activation = build_sandbox_event(
        store,
        "paper-sandbox",
        action="ACTIVATE",
        configuration_id=configuration_id,
        operator="owner",
        note="Activate without clearing runtime switch.",
        event_at=START + timedelta(hours=1),
    )
    store.archive_isolated_paper_sandbox_event(activation)
    with pytest.raises(ValueError, match="not explicitly clear"):
        _acquire(store)

    store.set_isolated_paper_runtime_kill_switch(
        "paper-sandbox",
        action="CLEAR",
        operator="owner",
        note="Explicitly permit isolated PAPER_ONLY runtime.",
        now=START + timedelta(hours=1, minutes=1),
    )
    acquired = _acquire(store)
    assert acquired["configuration_id"] == configuration_id
    assert acquired["live_execution_allowed"] is False
    assert acquired["fencing_token"] == TOKEN
    with pytest.raises(ValueError, match="fencing token"):
        run_isolated_runtime_cycle(
            store,
            acquired["session_id"],
            "wrong-runtime-fencing-token",
            lease_seconds=30,
            now=START + timedelta(hours=2, seconds=5),
        )
    cycle = run_isolated_runtime_cycle(
        store,
        acquired["session_id"],
        TOKEN,
        lease_seconds=30,
        now=START + timedelta(hours=2, seconds=10),
    )
    assert cycle["effective_status"] == "RUNNING"
    assert cycle["configuration_consumed"] is True
    assert cycle["paper_calculation_performed"] is False
    assert "fencing_token" not in cycle
    assert len(store.list_isolated_paper_runtime_events(acquired["session_id"])) == 2
    with pytest.raises(ValueError, match="already has a running leased session"):
        _acquire(store, at=START + timedelta(hours=2, seconds=20), token=TOKEN + "-b")


def test_expired_lease_is_immediate_on_read_and_reconciled_without_get_write(
    tmp_path: Path, monkeypatch
):
    store, *_ = _active_store(tmp_path, monkeypatch)
    acquired = _acquire(store)
    before = store.list_isolated_paper_runtime_events(acquired["session_id"])
    view = store.resolve_isolated_paper_runtime_session(
        acquired["session_id"], now=START + timedelta(hours=2, seconds=31)
    )
    assert view["stored_status"] == "RUNNING"
    assert view["effective_status"] == "LEASE_EXPIRED_FAIL_SAFE"
    assert store.list_isolated_paper_runtime_events(acquired["session_id"]) == before
    summary = store.reconcile_isolated_paper_runtime_sessions(
        now=START + timedelta(hours=2, seconds=31)
    )
    assert summary["records"][0]["status"] == "STOPPED"
    reconciled = store.resolve_isolated_paper_runtime_session(
        acquired["session_id"], now=START + timedelta(hours=2, seconds=31)
    )
    assert reconciled["stored_status"] == "STOPPED"
    assert reconciled["blocking_reason"] == "LEASE_EXPIRED"


def test_pointer_change_fences_old_worker_and_allows_atomic_takeover(
    tmp_path: Path, monkeypatch
):
    store, _, _, configuration_id, _ = _active_store(tmp_path, monkeypatch)
    acquired = _acquire(store)
    rollback = build_sandbox_event(
        store,
        "paper-sandbox",
        action="ROLLBACK",
        configuration_id=None,
        operator="owner",
        note="Fence the current runtime pointer.",
        event_at=START + timedelta(hours=2, seconds=5),
    )
    store.archive_isolated_paper_sandbox_event(rollback)
    activation = build_sandbox_event(
        store,
        "paper-sandbox",
        action="ACTIVATE",
        configuration_id=configuration_id,
        operator="owner",
        note="Reactivate under a new sandbox version.",
        event_at=START + timedelta(hours=2, seconds=6),
    )
    store.archive_isolated_paper_sandbox_event(activation)
    old = store.resolve_isolated_paper_runtime_session(
        acquired["session_id"], now=START + timedelta(hours=2, seconds=7)
    )
    assert old["effective_status"] == "POINTER_CHANGED_FAIL_SAFE"
    replacement = _acquire(
        store,
        at=START + timedelta(hours=2, seconds=7),
        token=TOKEN + "-replacement",
        worker="worker-b",
    )
    assert replacement["session_id"] != acquired["session_id"]
    assert store.resolve_isolated_paper_runtime_session(
        acquired["session_id"], now=START + timedelta(hours=2, seconds=7)
    )["stored_status"] == "STOPPED"
    assert store.resolve_isolated_paper_runtime_session(
        replacement["session_id"], now=START + timedelta(hours=2, seconds=7)
    )["effective_status"] == "RUNNING"


def test_kill_switch_arm_stops_session_atomically_and_clear_never_restarts(
    tmp_path: Path, monkeypatch
):
    store, *_ = _active_store(tmp_path, monkeypatch)
    acquired = _acquire(store)
    with pytest.raises(ValueError, match="cannot predate a running heartbeat"):
        store.set_isolated_paper_runtime_kill_switch(
            "paper-sandbox",
            action="ARM",
            operator="owner",
            note="Reject backdated kill-switch audit event.",
            now=START + timedelta(hours=1, minutes=30),
        )
    event_id = store.set_isolated_paper_runtime_kill_switch(
        "paper-sandbox",
        action="ARM",
        operator="owner",
        note="Immediate local PAPER_ONLY stop.",
        now=START + timedelta(hours=2, seconds=5),
    )
    switch = store.isolated_paper_runtime_kill_switch("paper-sandbox")
    session = store.resolve_isolated_paper_runtime_session(
        acquired["session_id"], now=START + timedelta(hours=2, seconds=5)
    )
    assert switch["latest_event_id"] == event_id
    assert switch["effective_state"] == "ARMED"
    assert session["stored_status"] == "STOPPED"
    assert session["blocking_reason"] == "KILL_SWITCH_ARMED"
    store.set_isolated_paper_runtime_kill_switch(
        "paper-sandbox",
        action="CLEAR",
        operator="owner",
        note="Clear only after review; do not restart automatically.",
        now=START + timedelta(hours=2, seconds=6),
    )
    assert store.resolve_isolated_paper_runtime_session(
        acquired["session_id"], now=START + timedelta(hours=2, seconds=7)
    )["stored_status"] == "STOPPED"
    assert [event["action"] for event in store.list_isolated_paper_runtime_kill_events(
        "paper-sandbox"
    )] == ["CLEAR", "ARM", "CLEAR"]


def test_bounded_runtime_consumes_configuration_without_replay_or_orders(
    tmp_path: Path, monkeypatch
):
    store, *_ = _active_store(tmp_path, monkeypatch)
    result = run_isolated_paper_runtime(
        store,
        "paper-sandbox",
        worker_id="bounded-worker",
        settings=IsolatedRuntimeSettings(
            lease_seconds=30, heartbeat_interval_seconds=10, max_cycles=2
        ),
        clock=lambda: START + timedelta(hours=2),
        sleeper=lambda _: None,
        token_factory=lambda: TOKEN,
    )
    assert result["paper_configuration_consumed"] is True
    assert len(result["cycles"]) == 2
    assert result["final_status"] == "STOPPED"
    assert result["replay_started"] is False
    assert result["order_path_present"] is False
    assert result["live_execution_allowed"] is False


def test_runtime_api_is_read_only_and_never_exposes_fencing_token(
    tmp_path: Path, monkeypatch
):
    store, *_ = _active_store(tmp_path, monkeypatch)
    acquired = _acquire(store)
    before = store.list_isolated_paper_runtime_events(acquired["session_id"])
    handler_type = make_handler(DashboardService(store), tmp_path)
    handler = object.__new__(handler_type)
    handler.path = "/api/v1/isolated-runtime?sandbox_id=paper-sandbox"
    status, overview = handler._api_payload()
    assert status == HTTPStatus.OK
    assert overview["read_only"] is True
    assert overview["live_execution_allowed"] is False
    assert "fencing_token" not in json.dumps(overview)
    handler.path = f"/api/v1/isolated-runtime-sessions/{acquired['session_id']}"
    status, session = handler._api_payload()
    assert status == HTTPStatus.OK
    assert session["effective_status"] != "RUNNING"  # wall clock is beyond test lease
    handler.path = f"/api/v1/isolated-runtime-events?session_id={acquired['session_id']}"
    status, events = handler._api_payload()
    assert status == HTTPStatus.OK
    assert events["events"][0]["action"] == "START"
    handler.path = "/api/v1/isolated-runtime-kill-events?sandbox_id=paper-sandbox"
    status, kill_events = handler._api_payload()
    assert status == HTTPStatus.OK
    assert kill_events["events"][0]["action"] == "CLEAR"
    assert store.list_isolated_paper_runtime_events(acquired["session_id"]) == before


def test_runtime_cli_is_explicit_bounded_and_paper_only(tmp_path: Path, monkeypatch):
    store, trial_id, _ = _approved_store(
        tmp_path,
        monkeypatch,
        validity_hours=48,
        approved_at=datetime.now(timezone.utc),
    )
    root = Path(__file__).parents[1]
    registry = root / "run_isolated_paper_config.py"
    runtime = root / "run_isolated_paper_runtime.py"
    registered = subprocess.run(
        [sys.executable, str(registry), "--db", store.path, "--action", "REGISTER",
         "--trial-id", trial_id],
        check=True, capture_output=True, text=True,
    )
    configuration_id = registered.stdout.split("configuration_id=", 1)[1].split()[0]
    subprocess.run(
        [sys.executable, str(registry), "--db", store.path, "--action", "ACTIVATE",
         "--configuration-id", configuration_id, "--sandbox-id", "paper-sandbox",
         "--operator", "owner", "--note", "Activate for bounded runtime CLI."],
        check=True, capture_output=True, text=True,
    )
    cleared = subprocess.run(
        [sys.executable, str(runtime), "--db", store.path, "--action", "CLEAR_KILL",
         "--sandbox-id", "paper-sandbox", "--operator", "owner", "--note",
         "Initialize runtime switch explicitly."],
        check=True, capture_output=True, text=True,
    )
    assert json.loads(cleared.stdout)["kill_switch"]["effective_state"] == "CLEAR"
    completed = subprocess.run(
        [sys.executable, str(runtime), "--db", store.path, "--action", "RUN",
         "--sandbox-id", "paper-sandbox", "--worker-id", "cli-worker",
         "--max-cycles", "1"],
        check=True, capture_output=True, text=True,
    )
    result = json.loads(completed.stdout)
    assert result["final_status"] == "STOPPED"
    assert result["paper_configuration_consumed"] is True
    assert result["replay_started"] is False
    assert result["order_path_present"] is False
    assert result["live_execution_allowed"] is False
    reconciled = subprocess.run(
        [sys.executable, str(runtime), "--db", store.path, "--action", "RECONCILE"],
        check=True, capture_output=True, text=True,
    )
    assert json.loads(reconciled.stdout)["records"] == []


def test_mil322_ui_exposes_actual_runtime_lease_kill_and_recovery_state():
    ui_root = Path(__file__).parents[1] / "ui"
    html = (ui_root / "index.html").read_text(encoding="utf-8")
    javascript = (ui_root / "app.js").read_text(encoding="utf-8")
    css = (ui_root / "styles.css").read_text(encoding="utf-8")
    assert "AARS // 03.22" in html
    assert 'id="runtime-effective-status"' in html
    assert 'id="runtime-kill-switch"' in html
    assert 'id="runtime-session-summary"' in html
    assert 'id="runtime-lease-health"' in html
    assert 'id="runtime-event-history"' in html
    assert 'id="runtime-kill-history"' in html
    assert "THIS SCREEN HAS NO RUN, STOP OR KILL-SWITCH BUTTON" in javascript
    assert "/api/v1/isolated-runtime?sandbox_id=${encodeURIComponent(sandboxId)}" in javascript
    assert "/api/v1/isolated-runtime-kill-events?sandbox_id=${encodeURIComponent(sandboxId)}" in javascript
    assert "isolated runtime effective state differs from stored authority" in javascript
    assert ".isolated-runtime-grid" in css
    assert 'type="button">RUN<' not in html
    assert 'type="button">STOP<' not in html
    assert 'type="button">ARM' not in html
