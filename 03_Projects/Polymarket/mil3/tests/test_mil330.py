from __future__ import annotations

import json
import subprocess
import sys
from datetime import timedelta
from http import HTTPStatus
from pathlib import Path

from aars_market.api import make_handler
from aars_market.frozen_monitor import (
    FrozenMonitorSettings,
    build_frozen_forward_evidence_view,
    run_frozen_evidence_cycle,
    run_frozen_evidence_scheduler,
)
from aars_market.robustness import RobustnessSettings
from aars_market.service import DashboardService
from tests.test_mil327 import _candles, _ready_store


ROBUSTNESS = RobustnessSettings(
    warmup_bars=60,
    test_bars=24,
    step_bars=24,
    discovery_window_bars=72,
    multi_windows=(("96h", 96), ("144h", 144), ("all", 181)),
    min_post_freeze_folds=2,
)
SETTINGS = FrozenMonitorSettings(robustness=ROBUSTNESS)


def _now(rows):
    return rows[-1].open_time + timedelta(hours=1, minutes=1)


def test_checkpoint_zero_is_exact_content_addressed_and_idempotent(tmp_path: Path):
    store, snapshot_id, snapshot = _ready_store(tmp_path)
    rows = _candles("BTCUSDT")

    first = run_frozen_evidence_cycle(
        store, snapshot_id=snapshot_id, settings=SETTINGS, now=_now(rows)
    )
    second = run_frozen_evidence_cycle(
        store, snapshot_id=snapshot_id, settings=SETTINGS, now=_now(rows)
    )

    assert first["status"] == "ARCHIVED"
    assert first["archived"][0]["post_freeze_fold_count"] == 0
    assert first["archived"][0]["validation_as_of"] == snapshot["as_of"]
    assert second["status"] == "WAITING"
    assert second["archived"] == []
    spec_hash = first["view"]["frozen_specification"]["spec_sha256"]
    checkpoints = store.load_frozen_robustness_checkpoints(spec_sha256=spec_hash)
    assert len(checkpoints) == 1
    payload = checkpoints[0][1]
    assert payload["post_freeze_fold_count"] == 0
    assert payload["robustness_report"]["validation_design"]["parameter_search_count"] == 0
    assert payload["authority"]["parameter_tuning_allowed"] is False
    assert payload["authority"]["proposal_creation_allowed"] is False
    assert payload["authority"]["challenger_activation_allowed"] is False
    assert payload["authority"]["live_execution_allowed"] is False


def test_new_complete_folds_are_caught_up_in_order_and_recalculate_fixed_gate(tmp_path: Path):
    store, snapshot_id, _ = _ready_store(tmp_path)
    original = _candles("BTCUSDT")
    run_frozen_evidence_cycle(
        store, snapshot_id=snapshot_id, settings=SETTINGS, now=_now(original)
    )
    extended = _candles("BTCUSDT", bars=281)
    store.upsert_candles(extended[181:], "mil330-forward")

    caught_up = run_frozen_evidence_cycle(
        store, snapshot_id=snapshot_id, settings=SETTINGS, now=_now(extended)
    )
    repeated = run_frozen_evidence_cycle(
        store, snapshot_id=snapshot_id, settings=SETTINGS, now=_now(extended)
    )

    assert [row["post_freeze_fold_count"] for row in caught_up["archived"]] == [1, 2, 3]
    assert [row["validation_as_of"] for row in caught_up["archived"]] == sorted(
        row["validation_as_of"] for row in caught_up["archived"]
    )
    assert repeated["status"] == "WAITING"
    collection = caught_up["view"]["collection"]
    assert collection["checkpoint_count"] == 4
    assert collection["latest_archived_post_freeze_fold_count"] == 3
    assert collection["new_checkpoint_count_due"] == 0
    latest_gate = caught_up["view"]["latest_robustness_gate"]
    post_check = next(
        row for row in latest_gate["checks"]
        if row["id"] == "POST_FREEZE_FORWARD_EVIDENCE"
    )
    assert post_check["observed"]["folds"] == 3
    assert post_check["requirement"] == ">= 2 folds and >= 50% win rate"
    latest_report = store.load_frozen_robustness_checkpoints(
        spec_sha256=caught_up["view"]["frozen_specification"]["spec_sha256"]
    )[-1][1]["robustness_report"]
    assert latest_report["validation_design"]["selection_uses_any_validation_fold"] is False
    assert latest_report["validation_design"]["parameter_search_count"] == 0


def test_forward_drift_alarms_are_actionable_and_never_recommend_tuning(tmp_path: Path):
    store, snapshot_id, _ = _ready_store(tmp_path)
    strict = FrozenMonitorSettings(
        robustness=ROBUSTNESS,
        state_mix_shift_limit=1e-12,
        state_outcome_deterioration_per_bar=1e-12,
        cost_return_deterioration_limit=1e-12,
        latest_fold_loss_limit=1e-12,
    )
    original = _candles("BTCUSDT")
    run_frozen_evidence_cycle(
        store, snapshot_id=snapshot_id, settings=strict, now=_now(original)
    )
    extended = _candles("BTCUSDT", bars=281)
    store.upsert_candles(extended[181:], "mil330-drift")

    cycle = run_frozen_evidence_cycle(
        store, snapshot_id=snapshot_id, settings=strict, now=_now(extended)
    )

    drift = cycle["view"]["drift"]
    assert drift["status"] == "ALERT"
    assert drift["highest_severity"] in {"HIGH", "CRITICAL"}
    assert drift["state_mix"]
    assert drift["state_outcomes"]
    assert drift["cost_sensitivity"]
    assert drift["alerts"]
    for alert in drift["alerts"]:
        assert alert["trigger"]
        assert alert["impact"]
        assert alert["evidence"]
        assert alert["recommended_response"]
        assert alert["closure_condition"]
        response = alert["recommended_response"].lower()
        assert any(
            boundary in response
            for boundary in ("do not retune", "frozen observation", "unchanged-policy")
        )
    assert cycle["view"]["review_gate"]["parameter_tuning_allowed"] is False
    assert cycle["view"]["review_gate"]["challenger_activation_allowed"] is False


def test_tamper_and_post_freeze_history_gap_fail_closed(tmp_path: Path):
    store, snapshot_id, _ = _ready_store(tmp_path / "tamper")
    original = _candles("BTCUSDT")
    cycle = run_frozen_evidence_cycle(
        store, snapshot_id=snapshot_id, settings=SETTINGS, now=_now(original)
    )
    checkpoint_id = cycle["archived"][0]["checkpoint_id"]
    with store.connect() as conn:
        row = conn.execute(
            "SELECT payload_json FROM frozen_robustness_checkpoints WHERE checkpoint_id=?",
            (checkpoint_id,),
        ).fetchone()
        tampered = json.loads(row["payload_json"])
        tampered["robustness_report"]["generated_at"] = "2099-01-01T00:00:00+00:00"
        conn.execute(
            "UPDATE frozen_robustness_checkpoints SET payload_json=? WHERE checkpoint_id=?",
            (json.dumps(tampered, sort_keys=True, separators=(",", ":")), checkpoint_id),
        )
    degraded = build_frozen_forward_evidence_view(
        store, snapshot_id=snapshot_id, settings=SETTINGS, observed_at=_now(original)
    )
    assert degraded["status"] == "DEGRADED"
    assert "hash verification" in degraded["data_trust"]["reason"]
    assert degraded["review_gate"]["live_execution_allowed"] is False

    gap_store, gap_snapshot_id, _ = _ready_store(tmp_path / "gap")
    extended = _candles("BTCUSDT", bars=220)
    gap_store.upsert_candles(extended[181:], "mil330-gap")
    with gap_store.connect() as conn:
        conn.execute(
            "DELETE FROM candles WHERE symbol=? AND timeframe=? AND open_time=?",
            ("BTCUSDT", "1h", extended[190].open_time.isoformat()),
        )
    gap = build_frozen_forward_evidence_view(
        gap_store,
        snapshot_id=gap_snapshot_id,
        settings=SETTINGS,
        observed_at=_now(extended),
    )
    assert gap["status"] == "DEGRADED"
    assert gap["data_trust"]["reason"] == "VALIDATION_HISTORY_GAP"


def test_scheduler_is_bounded_and_sleeps_only_between_cycles(tmp_path: Path):
    store, snapshot_id, _ = _ready_store(tmp_path)
    rows = _candles("BTCUSDT")
    sleeps = []

    cycles = run_frozen_evidence_scheduler(
        store,
        interval_seconds=1,
        max_cycles=2,
        snapshot_id=snapshot_id,
        settings=SETTINGS,
        clock=lambda: _now(rows),
        sleeper=sleeps.append,
    )

    assert [cycle["status"] for cycle in cycles] == ["ARCHIVED", "WAITING"]
    assert sleeps == [1]
    assert all(cycle["authority"]["live_execution_allowed"] is False for cycle in cycles)


def test_monitor_api_cli_and_hmi_are_read_only(tmp_path: Path):
    store, snapshot_id, _ = _ready_store(tmp_path)
    ui_root = Path(__file__).parents[1] / "ui"
    handler_type = make_handler(DashboardService(store), ui_root)
    handler = object.__new__(handler_type)
    handler.path = f"/api/v1/frozen-forward-evidence?snapshot_id={snapshot_id}"

    status, payload = handler._api_payload()

    assert status == HTTPStatus.OK
    assert payload["review_gate"]["disposition"] == "INITIAL_CHECKPOINT_REQUIRED"
    assert payload["data_trust"]["checkpoint_hashes_verified"] is False
    assert payload["collection"]["new_checkpoint_count_due"] == 1
    assert payload["collection"]["next_eligible_boundary"] == (
        payload["frozen_specification"]["frozen_at"]
    )
    assert payload["authority"]["read_only"] is True
    assert payload["authority"]["parameter_tuning_allowed"] is False
    completed = subprocess.run(
        [
            sys.executable,
            "run_frozen_evidence_monitor.py",
            "--db",
            str(store.path),
            "--snapshot-id",
            snapshot_id,
            "--action",
            "WAKE",
        ],
        cwd=Path(__file__).parents[1],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "monitor_scope=FROZEN_WEEKLY_EVIDENCE_ONLY" in completed.stdout
    assert "parameter_tuning_allowed=false proposal_creation_allowed=false" in completed.stdout
    assert "challenger_activation_allowed=false live_execution_allowed=false" in completed.stdout

    html = (ui_root / "index.html").read_text(encoding="utf-8")
    javascript = (ui_root / "app.js").read_text(encoding="utf-8")
    css = (ui_root / "styles.css").read_text(encoding="utf-8")
    assert 'id="frozen-forward-progress"' in html
    assert 'id="frozen-forward-next"' in html
    assert 'id="frozen-forward-alerts"' in html
    assert 'id="frozen-forward-history"' in html
    assert "/api/v1/frozen-forward-evidence" in javascript
    assert "authority.parameter_tuning_allowed !== false" in javascript
    assert "authority.challenger_activation_allowed !== false" in javascript
    assert ".frozen-forward-deck" in css
    assert '.frozen-forward-alerts article[data-severity="CRITICAL"]' in css
