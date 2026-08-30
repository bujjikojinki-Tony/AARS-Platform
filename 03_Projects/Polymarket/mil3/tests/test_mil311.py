from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from aars_market.models import Candle
from aars_market.simulation import SimulationSummary
from aars_market.storage import MarketStore
from aars_market.validation import (
    ValidationCandidate,
    ValidationSettings,
    build_candidates,
    build_walk_forward_folds,
    combine_validation_reports,
    walk_forward_validate,
    write_validation_report,
)


START = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _candles(n: int = 300, symbol: str = "SOLUSDT") -> list[Candle]:
    return [
        Candle(
            symbol,
            "1h",
            START + timedelta(hours=index),
            100.0,
            102.0,
            98.0,
            100.0 + (1.0 if index % 2 else -1.0),
            1000.0,
        )
        for index in range(n)
    ]


def _summary(strategy: str, *, score: float, profit_factor: float = 1.0) -> SimulationSummary:
    return SimulationSummary(
        strategy=strategy,
        execution_mode="PAPER_ONLY",
        symbol="SOLUSDT",
        timeframe="1h",
        bars=40,
        initial_equity=1000.0,
        final_equity=1000.0 + score,
        total_return=score / 1000.0,
        max_drawdown=0.0,
        sharpe_approx=score,
        sortino=0.0,
        profit_factor=profit_factor,
        turnover_notional=0.0,
        fees=0.0,
        slippage=0.0,
        funding=0.0,
        realized_pnl=score,
        realized_grid_pnl=0.0,
        inventory_unrealized_pnl=0.0,
        final_net_exposure=0.0,
        max_abs_net_exposure=0.0,
        final_effective_leverage=0.0,
        max_effective_leverage=0.0,
        min_margin_buffer_pct=1.0,
        max_liquidation_risk=0.0,
        liquidation_events=0,
    )


def test_parameter_grids_are_deterministic_and_capped():
    candidates = build_candidates(
        "FUTURES_LONG_GRID",
        futures_leverages=(5.0, 2.0, 5.0),
        grid_spacings=(0.02, 0.01),
        grid_levels=(5,),
        tactical_hedges=(False, True),
    )

    assert len(candidates) == 8
    assert candidates[0].candidate_id == (
        "FUTURES_LONG_GRID:leverage=2:spacing=0.01:levels=5:hedge=on"
    )
    assert len({item.candidate_id for item in candidates}) == len(candidates)
    with pytest.raises(ValueError, match="cap=2"):
        build_candidates(
            "FUTURES_LONG_GRID",
            futures_leverages=(2.0, 5.0),
            grid_spacings=(0.01,),
            grid_levels=(3,),
            tactical_hedges=(True, False),
            candidate_cap=2,
        )


def test_walk_forward_folds_are_chronological_with_test_only_after_train():
    folds = build_walk_forward_folds(
        _candles(260), warmup_bars=60, train_bars=100, test_bars=40, step_bars=40
    )

    assert len(folds) == 2
    assert folds[0].train_start == 59
    assert folds[0].train_end == folds[0].test_start == 159
    assert folds[0].test_context_start == 100
    assert folds[0].test_end == 199
    assert folds[1].train_context_start == 40
    assert folds[1].test_start == 199
    assert all(fold.train_end <= fold.test_start for fold in folds)


def test_validation_rejects_mixed_or_non_chronological_candles():
    candidates = [ValidationCandidate("AARS_DYNAMIC", aars_max_abs_exposure=0.5)]
    mixed = _candles(199)
    mixed[-1] = Candle(
        "BTCUSDT",
        mixed[-1].timeframe,
        mixed[-1].open_time,
        mixed[-1].open,
        mixed[-1].high,
        mixed[-1].low,
        mixed[-1].close,
        mixed[-1].volume,
    )
    with pytest.raises(ValueError, match="one symbol"):
        walk_forward_validate(
            mixed,
            candidates,
            train_bars=100,
            test_bars=40,
            settings=ValidationSettings(warmup_bars=60),
        )
    reversed_pair = _candles(199)
    reversed_pair[50], reversed_pair[51] = reversed_pair[51], reversed_pair[50]
    with pytest.raises(ValueError, match="strictly chronological"):
        walk_forward_validate(
            reversed_pair,
            candidates,
            train_bars=100,
            test_bars=40,
            settings=ValidationSettings(warmup_bars=60),
        )


def test_parameter_selection_uses_training_only_even_when_test_favors_another_candidate():
    candidates = (
        ValidationCandidate("AARS_DYNAMIC", aars_max_abs_exposure=0.5),
        ValidationCandidate("AARS_DYNAMIC", aars_max_abs_exposure=1.0),
    )
    test_calls: list[str] = []

    def evaluator(candles, candidate, _settings):
        if len(candles) == 159:
            score = 2.0 if candidate.aars_max_abs_exposure == 0.5 else 1.0
        else:
            test_calls.append(candidate.candidate_id)
            score = 100.0 if candidate.aars_max_abs_exposure == 1.0 else -1.0
        return _summary(candidate.candidate_id, score=score)

    payload = walk_forward_validate(
        _candles(199),
        candidates,
        train_bars=100,
        test_bars=40,
        settings=ValidationSettings(warmup_bars=60),
        evaluator=evaluator,
        generated_at=START,
    )

    assert payload["selection_policy"]["uses_test_for_selection"] is False
    assert payload["folds"][0]["selected_candidate"]["candidate_id"].endswith(
        "exposure=0.5"
    )
    assert not any(item.endswith("exposure=1") for item in test_calls)
    assert test_calls == ["AARS_DYNAMIC:exposure=0.5", "BUY_HOLD"]


def test_validation_warns_on_small_single_candidate_sample_and_serializes_infinity(
    tmp_path: Path,
):
    candidate = ValidationCandidate("AARS_DYNAMIC", aars_max_abs_exposure=0.5)

    def evaluator(_candles, selected, _settings):
        return _summary(selected.candidate_id, score=1.0, profit_factor=float("inf"))

    payload = walk_forward_validate(
        _candles(199),
        [candidate],
        train_bars=100,
        test_bars=40,
        settings=ValidationSettings(warmup_bars=60),
        evaluator=evaluator,
        generated_at=START,
    )
    target = tmp_path / "validation.json"
    write_validation_report(str(target), payload)
    encoded = target.read_text(encoding="utf-8")

    assert {item["code"] for item in payload["warnings"]} >= {
        "INSUFFICIENT_FOLDS",
        "NO_PARAMETER_SENSITIVITY",
        "FUNDING_HISTORY_FALLBACK",
    }
    assert payload["review_gate"]["disposition"] == "DEFER"
    assert "Infinity" not in encoded
    assert json.loads(encoded)["folds"][0]["test_summary"]["profit_factor"] is None


def test_real_replay_validation_keeps_common_paper_ledger_metrics():
    payload = walk_forward_validate(
        _candles(299),
        build_candidates(
            "SPOT_GRID", grid_spacings=(0.01, 0.02), grid_levels=(2,)
        ),
        train_bars=80,
        test_bars=40,
        settings=ValidationSettings(
            warmup_bars=60, fee_rate=0.0005, slippage_rate=0.0002
        ),
        generated_at=START,
    )

    assert payload["execution_mode"] == "PAPER_ONLY"
    assert payload["aggregate"]["folds"] == 4
    summary = payload["folds"][0]["test_summary"]
    assert summary["strategy"] == "SPOT_GRID"
    assert summary["fees"] >= 0
    assert summary["slippage"] >= 0
    assert "max_liquidation_risk" in summary
    assert payload["review_gate"]["live_execution_allowed"] is False


def test_multi_asset_report_preserves_each_market_and_combines_evidence():
    candidates = build_candidates(
        "SPOT_GRID", grid_spacings=(0.01,), grid_levels=(2,)
    )
    reports = [
        walk_forward_validate(
            _candles(199, symbol),
            candidates,
            train_bars=100,
            test_bars=40,
            settings=ValidationSettings(warmup_bars=60),
            generated_at=START,
        )
        for symbol in ("BTCUSDT", "ETHUSDT", "SOLUSDT")
    ]

    payload = combine_validation_reports(reports, generated_at=START)

    assert payload["schema_version"] == "mil3.robustness-validation-batch.v1"
    assert payload["aggregate"]["assets"] == 3
    assert payload["aggregate"]["symbols"] == ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    assert payload["aggregate"]["total_folds"] == 3
    assert len(payload["markets"]) == 3
    assert payload["review_gate"]["live_execution_allowed"] is False


def test_validation_cli_writes_strict_json_report(tmp_path: Path):
    db = tmp_path / "market.sqlite"
    store = MarketStore(db)
    store.init_db()
    for symbol in ("BTCUSDT", "ETHUSDT", "SOLUSDT"):
        store.upsert_candles(_candles(199, symbol), "test")
    report = tmp_path / "report.json"
    runner = Path(__file__).parents[1] / "run_validate.py"

    result = subprocess.run(
        [
            sys.executable,
            str(runner),
            "--db",
            str(db),
            "--symbols",
            "BTCUSDT",
            "ETHUSDT",
            "SOLUSDT",
            "--strategy",
            "AARS_DYNAMIC",
            "--warmup",
            "60",
            "--train-bars",
            "100",
            "--test-bars",
            "40",
            "--aars-exposures",
            "0.5,1",
            "--output-json",
            str(report),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(report.read_text(encoding="utf-8"))
    assert "execution_mode=PAPER_ONLY" in result.stdout
    assert payload["schema_version"] == "mil3.robustness-validation-batch.v1"
    assert payload["aggregate"]["assets"] == 3
    assert all(
        market["selection_policy"]["uses_test_for_selection"] is False
        for market in payload["markets"]
    )
