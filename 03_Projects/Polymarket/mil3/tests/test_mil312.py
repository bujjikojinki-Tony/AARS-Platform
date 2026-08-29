from __future__ import annotations

import copy
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from pathlib import Path

import pytest

from aars_market.api import make_handler
from aars_market.models import Candle, FundingRate
from aars_market.service import DashboardService
from aars_market.shadow import build_shadow_daily_snapshot, build_shadow_stability
from aars_market.storage import MarketStore
from aars_market.validation import ValidationSettings, build_candidates


START = datetime(2026, 1, 1, tzinfo=timezone.utc)
SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")


def _snapshot(
    *,
    generated_at: str = "2026-01-10T00:00:00+00:00",
    as_of: str = "2026-01-09T23:00:00+00:00",
    candidate: str = "AARS_DYNAMIC:exposure=0.5",
    warnings: tuple[str, ...] = (),
    disposition: str = "READY_FOR_SHADOW_REVIEW",
    total_return: float = 0.1,
) -> dict:
    market = {
        "generated_at": generated_at,
        "market": {"symbol": "SOLUSDT"},
        "folds": [
            {
                "selected_candidate": {"candidate_id": candidate},
                "generated_at": generated_at,
            }
        ],
        "aggregate": {
            "mean_test_return": total_return,
            "selection_stability": 0.75,
        },
        "warnings": [
            {"code": code, "severity": "HIGH", "detail": code} for code in warnings
        ],
    }
    return {
        "schema_version": "mil3.shadow-daily.v1",
        "execution_mode": "PAPER_ONLY",
        "generated_at": generated_at,
        "as_of": as_of,
        "symbols": ["SOLUSDT"],
        "configuration": {
            "validation_strategy": "AARS_DYNAMIC",
            "portfolio_strategy": "AARS_DYNAMIC",
        },
        "validation": {"markets": [market]},
        "portfolio": {
            "generated_at": generated_at,
            "summary": {
                "total_return": total_return,
                "max_drawdown": 0.05,
                "final_net_exposure": 0.4,
                "final_gross_exposure": 0.4,
                "final_effective_leverage": 0.4,
                "min_margin_buffer_pct": 0.6,
                "max_liquidation_risk": 0.02,
                "liquidation_events": 0,
                "degraded": disposition == "DEFER",
            },
        },
        "review_gate": {
            "disposition": disposition,
            "live_execution_allowed": False,
        },
    }


def _seed_store(path: Path, bars: int = 199) -> MarketStore:
    store = MarketStore(path)
    store.init_db()
    for symbol in SYMBOLS:
        candles = [
            Candle(
                symbol,
                "1h",
                START + timedelta(hours=index),
                100.0,
                101.0,
                99.0,
                100.0 + (index % 7) * 0.1,
                1000.0,
            )
            for index in range(bars)
        ]
        store.upsert_candles(candles, "test")
        store.upsert_funding_rates(
            [
                FundingRate(symbol, START + timedelta(hours=index), 0.0001, 100.0)
                for index in range(0, bars, 8)
            ],
            "test",
        )
    return store


def test_shadow_archive_is_content_addressed_and_ignores_nested_generation_times(
    tmp_path: Path,
):
    store = MarketStore(tmp_path / "market.sqlite")
    store.init_db()
    first = _snapshot()
    second = copy.deepcopy(first)
    second["generated_at"] = "2026-01-11T00:00:00+00:00"
    second["validation"]["markets"][0]["generated_at"] = second["generated_at"]
    second["validation"]["markets"][0]["folds"][0]["generated_at"] = second[
        "generated_at"
    ]
    second["portfolio"]["generated_at"] = second["generated_at"]

    first_id = store.archive_shadow_daily_snapshot(first, created_at=START)
    second_id = store.archive_shadow_daily_snapshot(
        second, created_at=START + timedelta(days=1)
    )

    assert first_id == second_id
    assert len(store.list_shadow_daily_snapshots()) == 1
    assert store.get_shadow_daily_snapshot(first_id) == first

    changed = copy.deepcopy(second)
    changed["as_of"] = "2026-01-10T23:00:00+00:00"
    assert store.archive_shadow_daily_snapshot(changed) != first_id
    assert len(store.list_shadow_daily_snapshots()) == 2


def test_shadow_archive_rejects_non_paper_or_live_enabled_payload(tmp_path: Path):
    store = MarketStore(tmp_path / "market.sqlite")
    store.init_db()
    live = _snapshot()
    live["review_gate"]["live_execution_allowed"] = True
    with pytest.raises(ValueError, match="disallow live execution"):
        store.archive_shadow_daily_snapshot(live)
    wrong_mode = _snapshot()
    wrong_mode["execution_mode"] = "LIVE"
    with pytest.raises(ValueError, match="PAPER_ONLY"):
        store.archive_shadow_daily_snapshot(wrong_mode)


def test_shadow_archive_rejects_second_observation_for_same_target_utc_day(
    tmp_path: Path,
):
    store = MarketStore(tmp_path / "market.sqlite")
    store.init_db()
    first = _snapshot(as_of="2026-01-09T22:00:00+00:00")
    second = _snapshot(as_of="2026-01-09T23:00:00+00:00", total_return=0.2)

    store.archive_shadow_daily_snapshot(first, created_at=START)
    with pytest.raises(ValueError, match="already archived"):
        store.archive_shadow_daily_snapshot(
            second, created_at=START + timedelta(hours=1)
        )

    assert len(store.list_shadow_daily_snapshots()) == 1


def test_daily_builder_reuses_validation_and_portfolio_without_archiving(tmp_path: Path):
    store = _seed_store(tmp_path / "market.sqlite")
    now = START + timedelta(hours=199, minutes=30)

    payload = build_shadow_daily_snapshot(
        store,
        build_candidates(
            "SPOT_GRID", grid_spacings=(0.01, 0.02), grid_levels=(2,)
        ),
        train_bars=100,
        test_bars=40,
        settings=ValidationSettings(warmup_bars=60),
        replay_window="30d",
        now=now,
    )

    assert payload["schema_version"] == "mil3.shadow-daily.v2"
    assert payload["execution_mode"] == "PAPER_ONLY"
    assert payload["as_of"] == (START + timedelta(hours=198)).isoformat()
    assert payload["observation_date"] == "2026-01-09"
    assert payload["evidence_boundary"]["fully_closed"] is True
    assert payload["evidence_boundary"]["synchronized_closed_open_time"] == (
        START + timedelta(hours=198)
    ).isoformat()
    assert set(payload["evidence_as_of"].values()) == {payload["as_of"]}
    assert payload["validation"]["aggregate"]["assets"] == 3
    assert payload["portfolio"]["schema_version"] == "mil3.portfolio.v1"
    assert payload["configuration"]["validation_strategy"] == "SPOT_GRID"
    assert payload["configuration"]["portfolio_strategy"] == "AARS_DYNAMIC"
    assert payload["review_gate"]["live_execution_allowed"] is False
    assert store.list_shadow_daily_snapshots() == []


def test_daily_builder_excludes_still_open_candle_mutations(tmp_path: Path):
    store = _seed_store(tmp_path / "market.sqlite", bars=200)
    now = START + timedelta(hours=199, minutes=30)
    candidates = build_candidates(
        "SPOT_GRID", grid_spacings=(0.01,), grid_levels=(2,)
    )
    kwargs = {
        "train_bars": 100,
        "test_bars": 40,
        "settings": ValidationSettings(warmup_bars=60),
        "replay_window": "30d",
        "now": now,
    }

    before = build_shadow_daily_snapshot(store, candidates, **kwargs)
    for symbol in SYMBOLS:
        store.upsert_candles(
            [
                Candle(
                    symbol,
                    "1h",
                    START + timedelta(hours=199),
                    100.0,
                    250.0,
                    1.0,
                    200.0,
                    999999.0,
                )
            ],
            "still-open-mutation",
        )
    after = build_shadow_daily_snapshot(store, candidates, **kwargs)

    assert before == after
    assert before["as_of"] == (START + timedelta(hours=198)).isoformat()


def test_stability_timeline_reports_candidate_warning_and_review_transitions():
    first = _snapshot(warnings=("FUNDING_HISTORY_FALLBACK",), disposition="DEFER")
    second = _snapshot(
        as_of="2026-01-10T23:00:00+00:00",
        candidate="AARS_DYNAMIC:exposure=1",
        warnings=("PARAMETER_INSTABILITY",),
        total_return=0.12,
    )

    payload = build_shadow_stability(
        [("first", first), ("second", second)], generated_at=START
    )

    transition = payload["transitions"][0]
    assert payload["execution_mode"] == "PAPER_ONLY"
    assert transition["candidate_changes"][0]["symbol"] == "SOLUSDT"
    assert transition["warnings_added"] == ["PARAMETER_INSTABILITY"]
    assert transition["warnings_resolved"] == ["FUNDING_HISTORY_FALLBACK"]
    assert transition["review_transition"] == {
        "before": "DEFER",
        "after": "READY_FOR_SHADOW_REVIEW",
    }
    assert payload["summary"]["parameter_change_events"] == 1
    assert payload["summary"]["history_warnings"] == [
        "INSUFFICIENT_DAILY_HISTORY",
        "PARAMETER_CHURN",
    ]
    assert payload["summary"]["promotion_eligible_snapshot_count"] == 0
    assert payload["summary"]["excluded_legacy_snapshot_count"] == 2
    assert payload["review_gate"]["live_execution_allowed"] is False


def test_stability_keeps_legacy_history_but_only_v2_closed_evidence_is_eligible():
    legacy = _snapshot()
    closed = _snapshot(as_of="2026-01-10T23:00:00+00:00")
    closed["schema_version"] = "mil3.shadow-daily.v2"
    closed["observation_date"] = "2026-01-10"
    closed["evidence_as_of"] = {"SOLUSDT": closed["as_of"]}
    closed["evidence_boundary"] = {
        "observed_at": "2026-01-11T00:30:00+00:00",
        "synchronized_closed_open_time": closed["as_of"],
        "per_asset_closed_open_time": {"SOLUSDT": closed["as_of"]},
        "timeframe_duration_seconds": 3600.0,
        "fully_closed": True,
    }

    payload = build_shadow_stability(
        [("legacy", legacy), ("closed", closed)], generated_at=START
    )

    assert payload["snapshot_count"] == 2
    assert len(payload["points"]) == 2
    assert [
        point["snapshot_id"] for point in payload["promotion_eligible_points"]
    ] == ["closed"]
    assert payload["summary"]["promotion_eligible_snapshot_count"] == 1
    assert payload["summary"]["excluded_legacy_snapshot_count"] == 1

    unclosed = copy.deepcopy(closed)
    unclosed["evidence_boundary"]["observed_at"] = unclosed["as_of"]
    rejected = build_shadow_stability(
        [("unclosed", unclosed)], generated_at=START
    )
    assert rejected["promotion_eligible_points"] == []
    assert rejected["summary"]["excluded_legacy_snapshot_count"] == 1


def test_shadow_api_is_read_only_and_missing_snapshot_is_404(tmp_path: Path):
    store = MarketStore(tmp_path / "market.sqlite")
    store.init_db()
    snapshot_id = store.archive_shadow_daily_snapshot(_snapshot(), created_at=START)
    handler_type = make_handler(DashboardService(store), tmp_path)
    handler = object.__new__(handler_type)

    handler.path = "/api/v1/shadow-snapshots"
    status, index = handler._api_payload()
    assert status == HTTPStatus.OK
    assert index["read_only"] is True
    assert index["shadow_snapshots"][0]["snapshot_id"] == snapshot_id

    handler.path = f"/api/v1/shadow-snapshots/{snapshot_id}"
    status, loaded = handler._api_payload()
    assert status == HTTPStatus.OK
    assert loaded["execution_mode"] == "PAPER_ONLY"

    handler.path = "/api/v1/shadow-stability"
    status, stability = handler._api_payload()
    assert status == HTTPStatus.OK
    assert stability["snapshot_count"] == 1
    assert len(store.list_shadow_daily_snapshots()) == 1

    handler.path = "/api/v1/shadow-snapshots/missing"
    status, error = handler._api_payload()
    assert status == HTTPStatus.NOT_FOUND
    assert error == {"error": "shadow snapshot not found"}


def test_daily_cli_is_the_explicit_idempotent_archive_path(tmp_path: Path):
    db = tmp_path / "market.sqlite"
    store = _seed_store(db)
    runner = Path(__file__).parents[1] / "run_shadow_daily.py"
    command = [
        sys.executable,
        str(runner),
        "--db",
        str(db),
        "--validation-strategy",
        "SPOT_GRID",
        "--grid-spacings",
        "0.01",
        "--grid-levels",
        "2",
        "--warmup",
        "60",
        "--train-bars",
        "100",
        "--test-bars",
        "40",
        "--window",
        "30d",
    ]

    first = subprocess.run(command, check=True, capture_output=True, text=True)
    second = subprocess.run(command, check=True, capture_output=True, text=True)

    assert "execution_mode=PAPER_ONLY" in first.stdout
    assert "immutable=true" in first.stdout
    assert "snapshots_stored=1" in second.stdout
    assert len(store.list_shadow_daily_snapshots()) == 1
