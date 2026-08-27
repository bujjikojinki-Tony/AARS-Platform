from __future__ import annotations

import json
import subprocess
import sys
from datetime import timedelta
from http import HTTPStatus
from pathlib import Path

import pytest

from aars_market.api import make_handler
from aars_market.forward_monitor import (
    ForwardMonitorSettings,
    run_forward_monitor,
    run_forward_monitor_cycle,
)
from aars_market.forward_stability import (
    ForwardStabilityPolicy,
    build_forward_stability,
)
from aars_market.service import DashboardService
from tests.test_mil316 import START
from tests.test_mil317 import _eligible_trial


def _aggregate(*, score: float, return_value: float, risk: float = 0.01) -> dict:
    return {
        "mean_sharpe_approx": score,
        "mean_sortino": 0.0,
        "mean_total_return": return_value,
        "worst_max_drawdown": 0.05,
        "max_liquidation_risk": risk,
        "liquidation_events": 0,
    }


def _checkpoint(
    index: int,
    *,
    score: float = 0.5,
    return_delta: float = 0.02,
    risk: float = 0.01,
    previous_id: str | None = None,
    previous_hash: str | None = None,
    stopped: bool = False,
) -> tuple[str, dict]:
    observation_id = f"observation-{index}"
    input_hash = f"{index + 1:064x}"
    baseline = _aggregate(score=0.0, return_value=0.0)
    proposed = _aggregate(score=score, return_value=return_delta, risk=risk)
    return observation_id, {
        "schema_version": "mil3.forward-observation.v1",
        "execution_mode": "PAPER_ONLY",
        "trial_id": "trial-1",
        "target_strategy": "AARS_DYNAMIC",
        "boundary": {
            "synchronized_forward_end": (START + timedelta(days=index)).isoformat(),
        },
        "lineage": {
            "previous_observation_id": previous_id,
            "previous_input_sha256": previous_hash,
        },
        "input_evidence": {"combined_sha256": input_hash},
        "results": {
            "forward_bars": 720 + index * 24,
            "baseline": baseline,
            "proposed": proposed,
            "delta_proposed_minus_baseline": {
                "mean_total_return": return_delta,
                "worst_max_drawdown": 0.0,
            },
        },
        "stop_condition": {
            "triggered": stopped,
            "reasons": ["MAX_DRAWDOWN_LIMIT_EXCEEDED"] if stopped else [],
        },
        "review_gate": {
            "disposition": "STOP_FORWARD_OBSERVATION" if stopped else "PROPOSED_EDGE_CONFIRMED",
            "observation_application_allowed": False,
            "automatic_strategy_change_allowed": False,
            "live_execution_allowed": False,
        },
        "authority": {
            "observation_application_allowed": False,
            "automatic_strategy_change_allowed": False,
            "live_execution_allowed": False,
        },
    }


def _chain(count: int, **last_overrides: object) -> list[tuple[str, dict]]:
    items = []
    previous_id = None
    previous_hash = None
    for index in range(count):
        kwargs = last_overrides if index == count - 1 else {}
        item = _checkpoint(
            index,
            previous_id=previous_id,
            previous_hash=previous_hash,
            **kwargs,
        )
        items.append(item)
        previous_id = item[0]
        previous_hash = item[1]["input_evidence"]["combined_sha256"]
    return items


def test_stability_requires_horizon_and_consecutive_confirmations():
    payload = build_forward_stability(
        _chain(3),
        policy=ForwardStabilityPolicy(
            minimum_forward_bars=720,
            minimum_consecutive_qualifying=3,
        ),
        generated_at=START,
    )

    assert payload["schema_version"] == "mil3.forward-stability.v1"
    assert payload["summary"]["consecutive_qualifying_checkpoints"] == 3
    assert payload["review_gate"]["disposition"] == "EXTENDED_OBSERVATION_CONFIRMED"
    assert payload["review_gate"]["observation_application_allowed"] is False
    assert payload["review_gate"]["live_execution_allowed"] is False
    json.dumps(payload, allow_nan=False)

    short = _chain(3)
    for _, point in short:
        point["results"]["forward_bars"] = 200
    waiting = build_forward_stability(short, generated_at=START)
    assert "INSUFFICIENT_OBSERVATION_HORIZON" in waiting["summary"]["warning_codes"]
    assert waiting["review_gate"]["disposition"] == "CONTINUE_EXTENDED_OBSERVATION"


def test_stability_surfaces_decay_reversal_rising_risk_and_stop():
    items = _chain(3)
    for index, (_, point) in enumerate(items):
        point["results"]["proposed"] = _aggregate(
            score=(0.8, 0.4, -0.4)[index],
            return_value=(0.05, 0.02, -0.03)[index],
            risk=(0.01, 0.03, 0.06)[index],
        )
        point["results"]["delta_proposed_minus_baseline"]["mean_total_return"] = (
            0.05, 0.02, -0.03
        )[index]
    payload = build_forward_stability(items, generated_at=START)
    assert payload["summary"]["warning_codes"] == [
        "PROPOSED_EDGE_DECAY",
        "PROPOSED_EDGE_REVERSAL",
        "LIQUIDATION_RISK_RISING",
    ]
    assert {alarm["severity"] for alarm in payload["alarms"]} == {"MEDIUM", "HIGH"}
    assert payload["review_gate"]["disposition"] == "CONTINUE_EXTENDED_OBSERVATION"

    stopped = _chain(3, stopped=True)
    stop_payload = build_forward_stability(stopped, generated_at=START)
    assert stop_payload["review_gate"]["disposition"] == "STOP_EXTENDED_OBSERVATION"
    assert stop_payload["alarms"][-1]["severity"] == "CRITICAL"


def test_stability_defers_on_broken_lineage_or_checkpoint_gap():
    items = _chain(3)
    items[1][1]["lineage"]["previous_observation_id"] = "wrong"
    payload = build_forward_stability(items, generated_at=START)
    assert "CHECKPOINT_LINEAGE_BROKEN" in payload["summary"]["warning_codes"]
    assert payload["review_gate"]["disposition"] == "DEFER_EXTENDED_OBSERVATION"

    gap = _chain(2)
    gap[1][1]["boundary"]["synchronized_forward_end"] = (
        START + timedelta(days=5)
    ).isoformat()
    gap_payload = build_forward_stability(gap, generated_at=START)
    assert "CHECKPOINT_CADENCE_GAP" in gap_payload["summary"]["warning_codes"]


def test_monitor_cycle_archives_then_reuses_and_waits_safely(tmp_path: Path):
    store, trial_id, _ = _eligible_trial(tmp_path / "market.sqlite")
    settings = ForwardMonitorSettings(minimum_forward_bars=24, confirmation_bars=168)
    first = run_forward_monitor_cycle(store, settings=settings, now=START)
    second = run_forward_monitor_cycle(store, settings=settings, now=START + timedelta(hours=1))
    assert first["records"][0]["status"] == "ARCHIVED"
    assert second["records"][0]["status"] == "REUSED"
    assert first["records"][0]["trial_id"] == trial_id
    assert len(store.list_forward_observations(trial_id=trial_id)) == 1
    assert first["observation_application_allowed"] is False
    assert first["live_execution_allowed"] is False

    waiting_store, _, _ = _eligible_trial(tmp_path / "waiting.sqlite", total_bars=230)
    waiting = run_forward_monitor_cycle(waiting_store, settings=settings, now=START)
    assert waiting["status"] == "WAITING"
    assert waiting["records"][0]["status"] == "WAITING"


def test_monitor_loop_is_bounded_and_does_not_sleep_after_last_cycle(tmp_path: Path):
    store, _, _ = _eligible_trial(tmp_path / "market.sqlite")
    sleeps = []
    summaries = run_forward_monitor(
        store,
        interval_seconds=1,
        max_cycles=2,
        clock=lambda: START,
        sleeper=sleeps.append,
    )
    assert len(summaries) == 2
    assert sleeps == [1]


def test_forward_stability_api_is_read_only(tmp_path: Path):
    store, trial_id, _ = _eligible_trial(tmp_path / "market.sqlite")
    run_forward_monitor_cycle(store, now=START)
    handler_type = make_handler(DashboardService(store), tmp_path)
    handler = object.__new__(handler_type)
    handler.path = f"/api/v1/forward-stability?trial_id={trial_id}&limit=90"
    status, payload = handler._api_payload()
    assert status == HTTPStatus.OK
    assert payload["trial_id"] == trial_id
    assert payload["review_gate"]["observation_application_allowed"] is False
    assert payload["review_gate"]["live_execution_allowed"] is False

    handler.path = "/api/v1/forward-stability"
    with pytest.raises(ValueError, match="trial_id is required"):
        handler._api_payload()

    empty_store, empty_trial_id, _ = _eligible_trial(
        tmp_path / "empty.sqlite", total_bars=230
    )
    empty = DashboardService(empty_store).forward_stability(empty_trial_id)
    assert empty["trial_id"] == empty_trial_id
    assert empty["target_strategy"] == "AARS_DYNAMIC"
    assert empty["review_gate"]["disposition"] == "CONTINUE_EXTENDED_OBSERVATION"


def test_forward_monitor_cli_is_explicit_local_scheduler(tmp_path: Path):
    database = tmp_path / "market.sqlite"
    store, trial_id, _ = _eligible_trial(database)
    runner = Path(__file__).parents[1] / "run_forward_monitor.py"
    completed = subprocess.run(
        [
            sys.executable, str(runner), "--db", str(database),
            "--poll-seconds", "1", "--max-cycles", "1",
        ],
        check=True, capture_output=True, text=True,
    )
    assert "execution_mode=PAPER_ONLY" in completed.stdout
    assert "monitor_scope=IMMUTABLE_FORWARD_OBSERVATION_ONLY" in completed.stdout
    assert "observation_application_allowed=false" in completed.stdout
    assert "live_execution_allowed=false" in completed.stdout
    assert len(store.list_forward_observations(trial_id=trial_id)) == 1


def test_forward_stability_ui_keeps_progress_alarms_and_authority_visible():
    ui_root = Path(__file__).parents[1] / "ui"
    html = (ui_root / "index.html").read_text(encoding="utf-8")
    javascript = (ui_root / "app.js").read_text(encoding="utf-8")
    css = (ui_root / "styles.css").read_text(encoding="utf-8")
    assert "AARS // 03.21" in html
    assert 'id="forward-stability-status"' in html
    assert 'id="forward-stability-progress"' in html
    assert 'id="forward-stability-alarms"' in html
    assert "NO AUTO-PROMOTION" in html
    assert "/api/v1/forward-stability?trial_id=${encodeURIComponent(latest.trial_id)}" in javascript
    assert "forward stability did not preserve authority locks" in javascript
    assert "minimum_consecutive_qualifying" in javascript
    assert "recommended_action" in javascript
    assert "closure_condition" in javascript
    assert "Automatic strategy change and live execution remain disallowed" in javascript
    assert '.forward-stability-alarms article[data-severity="CRITICAL"]' in css
