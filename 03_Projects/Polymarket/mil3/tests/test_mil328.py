from __future__ import annotations

import json
import subprocess
import sys
from http import HTTPStatus
from pathlib import Path

import pytest

import aars_market.simulation as simulation
from aars_market.api import make_handler
from aars_market.challenger import build_low_turnover_challenger
from aars_market.models import MarketState, MarketStateAssessment, OutcomeProbabilities
from aars_market.policy import ExposureDecision
from aars_market.service import DashboardService
from aars_market.simulation import AarsDeadbandStrategy
from aars_market.storage import MarketStore
from tests.test_mil327 import _candles, _ready_store


def test_state_deadband_holds_noise_but_bypasses_direction_and_risk(monkeypatch):
    states = iter(
        (
            MarketState.RECOVERY,
            MarketState.RECOVERY,
            MarketState.RECOVERY,
            MarketState.DISTRIBUTION,
            MarketState.BREAKDOWN,
        )
    )
    targets = iter((0.20, 0.25, 0.35, 0.22, -0.40))
    monkeypatch.setattr(simulation, "compute_features", lambda _candles: object())
    monkeypatch.setattr(
        simulation,
        "classify_market_state",
        lambda _features: MarketStateAssessment(
            next(states), 0.8, ("test",), ()
        ),
    )
    monkeypatch.setattr(
        simulation,
        "estimate_outcome_probabilities",
        lambda *_args, **_kwargs: OutcomeProbabilities(0.4, 0.3, 0.3, 24),
    )
    monkeypatch.setattr(
        simulation,
        "decide_target_exposure",
        lambda *_args, **_kwargs: ExposureDecision(next(targets), "deterministic"),
    )
    deadbands = {state: 0.10 for state in MarketState}
    strategy = AarsDeadbandStrategy(
        exposure_scale=0.95,
        min_rebalance_bars=3,
        state_deadbands=deadbands,
    )
    candles = _candles("BTCUSDT")

    first = strategy.actions_for_bar(120, candles)
    noise = strategy.actions_for_bar(121, candles)
    interval_blocked = strategy.actions_for_bar(122, candles)
    risk_state = strategy.actions_for_bar(123, candles)
    defensive = strategy.actions_for_bar(124, candles)

    assert first[0].target_exposure == pytest.approx(0.19)
    assert noise == []
    assert interval_blocked == []
    assert risk_state[0].target_exposure == pytest.approx(0.209)
    assert "trigger=RISK_STATE" in risk_state[0].reason
    assert defensive[0].target_exposure == pytest.approx(-0.38)
    assert defensive[0].category == "tactical_short"
    assert "trigger=SIGN_CHANGE" in defensive[0].reason
    with pytest.raises(ValueError, match="exposure_scale"):
        AarsDeadbandStrategy(exposure_scale=1.1)
    with pytest.raises(ValueError, match="every MarketState"):
        AarsDeadbandStrategy(state_deadbands={MarketState.RANGE: 0.1})


def test_true_zero_cost_challenger_uses_identical_verified_boundary(tmp_path: Path):
    store, snapshot_id, _ = _ready_store(tmp_path)

    payload = build_low_turnover_challenger(store)

    assert payload["schema_version"] == "mil3.low-turnover-challenger.v1"
    assert payload["status"] == "READY"
    assert payload["data_trust"]["source_snapshot_id"] == snapshot_id
    assert payload["data_trust"]["comparison_boundary"] == (
        "IDENTICAL_FULLY_CLOSED_V2_EVIDENCE"
    )
    assert payload["configuration"]["zero_cost_model"]["kind"] == (
        "TRUE_ENGINE_RERUN_NOT_ACCOUNTING_ADD_BACK"
    )
    baseline = payload["comparison"]["baseline"]
    challenger = payload["comparison"]["challenger"]
    for result in (baseline["zero_cost"], challenger["zero_cost"]):
        assert result["fees"] == 0.0
        assert result["slippage"] == 0.0
        assert result["funding"] == 0.0
        assert result["modeled_cost_return"] == 0.0
    assert payload["comparison"]["deltas"]["actual_return"] == pytest.approx(
        challenger["actual_cost"]["total_return"]
        - baseline["actual_cost"]["total_return"]
    )
    assert payload["comparison"]["deltas"]["zero_cost_policy_return"] == pytest.approx(
        challenger["zero_cost"]["total_return"]
        - baseline["zero_cost"]["total_return"]
    )
    assert challenger["actual_cost"]["turnover_multiple"] < (
        baseline["actual_cost"]["turnover_multiple"]
    )
    assert payload["authority"]["challenger_activation_allowed"] is False
    assert payload["review_gate"]["requires_independent_validation"] is True
    assert payload["review_gate"]["proposal_creation_allowed"] is False
    json.dumps(payload, allow_nan=False)


def test_challenger_fails_closed_without_verified_v2_source(tmp_path: Path):
    store = MarketStore(tmp_path / "empty.sqlite")
    store.init_db()

    payload = build_low_turnover_challenger(store)

    assert payload["status"] == "DEGRADED"
    assert payload["comparison"] is None
    assert payload["review_gate"]["disposition"] == "DEFER"
    assert payload["authority"]["live_execution_allowed"] is False


def test_challenger_api_cli_and_hmi_are_read_only(tmp_path: Path):
    store, snapshot_id, _ = _ready_store(tmp_path)
    handler_type = make_handler(DashboardService(store), Path(__file__).parents[1] / "ui")
    handler = object.__new__(handler_type)
    handler.path = f"/api/v1/low-turnover-challenger?snapshot_id={snapshot_id}"

    status, payload = handler._api_payload()

    assert status == HTTPStatus.OK
    assert payload["authority"]["read_only"] is True
    assert payload["authority"]["automatic_strategy_change_allowed"] is False

    output = tmp_path / "challenger.json"
    completed = subprocess.run(
        [
            sys.executable,
            "run_low_turnover_challenger.py",
            "--db",
            str(store.path),
            "--output-json",
            str(output),
        ],
        cwd=Path(__file__).parents[1],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "execution_mode=PAPER_ONLY read_only=true" in completed.stdout
    assert "live_execution_allowed=false" in completed.stdout
    assert json.loads(output.read_text(encoding="utf-8"))["status"] == "READY"

    ui_root = Path(__file__).parents[1] / "ui"
    html = (ui_root / "index.html").read_text(encoding="utf-8")
    javascript = (ui_root / "app.js").read_text(encoding="utf-8")
    css = (ui_root / "styles.css").read_text(encoding="utf-8")
    assert 'id="challenger-disposition"' in html
    assert 'id="challenger-cost-matrix"' in html
    assert 'id="challenger-checks"' in html
    assert "TRUE ZERO-COST ENGINE RERUN" in html
    assert "/api/v1/low-turnover-challenger" in javascript
    assert "challenger_activation_allowed !== false" in javascript
    assert ".challenger-deck" in css
