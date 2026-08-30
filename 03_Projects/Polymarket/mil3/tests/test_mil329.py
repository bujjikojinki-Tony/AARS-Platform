from __future__ import annotations

import json
import subprocess
import sys
from datetime import timedelta
from http import HTTPStatus
from pathlib import Path

from aars_market.api import make_handler
from aars_market.robustness import (
    RobustnessSettings,
    build_frozen_challenger_robustness,
    frozen_specification,
)
from aars_market.service import DashboardService
from aars_market.storage import MarketStore
from tests.test_mil327 import _candles, _ready_store


SETTINGS = RobustnessSettings(
    warmup_bars=60,
    test_bars=24,
    step_bars=24,
    discovery_window_bars=72,
    multi_windows=(("96h", 96), ("144h", 144), ("all", 181)),
    min_post_freeze_folds=2,
)


def test_frozen_spec_is_content_addressed_and_has_no_tuning_surface():
    first = frozen_specification("snapshot-a", "2026-01-08T12:00:00+00:00")
    repeated = frozen_specification("snapshot-a", "2026-01-08T12:00:00+00:00")
    other_source = frozen_specification("snapshot-b", "2026-01-08T12:00:00+00:00")

    assert first == repeated
    assert first["spec_sha256"] != other_source["spec_sha256"]
    assert first["immutable"] is True
    assert first["validation_time_tuning_allowed"] is False
    assert first["parameters"]["min_rebalance_bars"] == 12
    assert first["parameters"]["exposure_scale"] == 0.95
    assert len(first["parameters"]["state_deadbands"]) == 7


def test_frozen_walk_forward_preserves_hash_lineage_stress_and_authority(tmp_path: Path):
    store, snapshot_id, snapshot = _ready_store(tmp_path)
    report = build_frozen_challenger_robustness(
        store,
        snapshot_id=snapshot_id,
        settings=SETTINGS,
    )

    assert report["schema_version"] == "mil3.frozen-challenger-robustness.v1"
    assert report["status"] == "READY"
    assert report["execution_mode"] == "PAPER_ONLY"
    assert report["data_trust"]["fully_closed"] is True
    assert report["validation_design"]["selection_uses_any_validation_fold"] is False
    assert report["validation_design"]["parameter_search_count"] == 0
    assert report["validation_design"]["frozen_at"] == snapshot["as_of"]
    spec_hash = report["frozen_specification"]["spec_sha256"]
    evidence_rows = [
        *report["multi_window"],
        *report["walk_forward"]["folds"],
        *report["stress_matrix"],
    ]
    assert evidence_rows
    assert {row["spec_sha256"] for row in evidence_rows} == {spec_hash}
    assert all(row["selection_uses_fold"] is False for row in report["walk_forward"]["folds"])
    assert {row["id"] for row in report["stress_matrix"]} == {
        "ACTUAL_1X",
        "EXECUTION_2X",
        "EXECUTION_3X",
        "ALL_MODELED_COST_2X",
    }
    assert report["market_state_evidence"]
    assert report["overfit_assessment"]["level"] == "HIGH"
    assert report["review_gate"]["disposition"] != "ROBUSTNESS_CANDIDATE"
    assert report["authority"] == {
        "read_only": True,
        "parameter_tuning_allowed": False,
        "proposal_creation_allowed": False,
        "challenger_activation_allowed": False,
        "automatic_strategy_change_allowed": False,
        "live_execution_allowed": False,
    }


def test_post_freeze_folds_accumulate_without_changing_frozen_identity(tmp_path: Path):
    store, snapshot_id, snapshot = _ready_store(tmp_path)
    initial = build_frozen_challenger_robustness(
        store, snapshot_id=snapshot_id, settings=SETTINGS
    )
    extended = _candles("BTCUSDT", bars=281)
    store.upsert_candles(extended[181:], "mil329-forward-test")

    report = build_frozen_challenger_robustness(
        store,
        snapshot_id=snapshot_id,
        settings=SETTINGS,
        observed_at=extended[-1].open_time + timedelta(hours=1, minutes=1),
    )

    assert report["frozen_specification"]["spec_sha256"] == (
        initial["frozen_specification"]["spec_sha256"]
    )
    post = next(
        row for row in report["walk_forward"]["lineage_summary"]
        if row["lineage"] == "POST_FREEZE_FORWARD"
    )
    assert post["folds"] >= 2
    assert report["overfit_assessment"]["level"] != "HIGH"
    assert all(
        row["selection_uses_fold"] is False
        for row in report["walk_forward"]["folds"]
        if row["lineage"] == "POST_FREEZE_FORWARD"
    )


def test_robustness_fails_closed_without_verified_source(tmp_path: Path):
    store = MarketStore(tmp_path / "empty.sqlite")
    store.init_db()

    report = build_frozen_challenger_robustness(store)

    assert report["status"] == "DEGRADED"
    assert report["frozen_specification"] is None
    assert report["review_gate"]["disposition"] == "DEFER"
    assert report["authority"]["parameter_tuning_allowed"] is False
    assert report["authority"]["live_execution_allowed"] is False


def test_robustness_api_cli_and_hmi_are_read_only(tmp_path: Path):
    store, snapshot_id, _ = _ready_store(tmp_path)
    ui_root = Path(__file__).parents[1] / "ui"
    handler_type = make_handler(DashboardService(store), ui_root)
    handler = object.__new__(handler_type)
    handler.path = f"/api/v1/frozen-challenger-robustness?snapshot_id={snapshot_id}"

    status, payload = handler._api_payload()

    assert status == HTTPStatus.OK
    assert payload["authority"]["read_only"] is True
    assert payload["authority"]["proposal_creation_allowed"] is False
    output = tmp_path / "robustness.json"
    completed = subprocess.run(
        [
            sys.executable,
            "run_frozen_challenger_robustness.py",
            "--db",
            str(store.path),
            "--snapshot-id",
            snapshot_id,
            "--output-json",
            str(output),
        ],
        cwd=Path(__file__).parents[1],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "execution_mode=PAPER_ONLY read_only=true parameter_tuning_allowed=false" in completed.stdout
    assert "live_execution_allowed=false" in completed.stdout
    assert json.loads(output.read_text(encoding="utf-8"))["status"] == "READY"

    html = (ui_root / "index.html").read_text(encoding="utf-8")
    javascript = (ui_root / "app.js").read_text(encoding="utf-8")
    css = (ui_root / "styles.css").read_text(encoding="utf-8")
    assert 'id="robustness-overfit"' in html
    assert 'id="robustness-lineage"' in html
    assert 'id="robustness-stress"' in html
    assert 'id="robustness-checks"' in html
    assert "/api/v1/frozen-challenger-robustness" in javascript
    assert "authority.parameter_tuning_allowed !== false" in javascript
    assert "authority.challenger_activation_allowed !== false" in javascript
    assert ".robustness-deck" in css
