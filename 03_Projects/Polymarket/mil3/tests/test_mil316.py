from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from pathlib import Path

import pytest

from aars_market.api import make_handler
from aars_market.models import Candle, FundingRate
from aars_market.proposal import (
    build_paper_configuration_proposal,
    build_paper_proposal_review,
)
from aars_market.service import DashboardService
from aars_market.storage import MarketStore
from aars_market.trial import PaperTrialSettings, build_paper_trial_result


START = datetime(2026, 1, 1, tzinfo=timezone.utc)
SYMBOLS = ("BTCUSDT", "ETHUSDT")


def _candidate(exposure: float) -> dict:
    return {
        "candidate_id": f"AARS_DYNAMIC:exposure={exposure:g}",
        "target_strategy": "AARS_DYNAMIC",
        "aars_max_abs_exposure": exposure,
        "futures_leverage": 10.0,
        "grid_spacing_pct": 0.01,
        "grid_levels": 5,
        "tactical_hedge": True,
    }


def _snapshot(last: datetime) -> dict:
    return {
        "schema_version": "mil3.shadow-daily.v1",
        "execution_mode": "PAPER_ONLY",
        "generated_at": last.isoformat(),
        "as_of": last.isoformat(),
        "symbols": list(SYMBOLS),
        "evidence_as_of": {symbol: last.isoformat() for symbol in SYMBOLS},
        "configuration": {
            "validation_strategy": "AARS_DYNAMIC",
            "portfolio_strategy": "AARS_DYNAMIC",
            "timeframe": "1h",
            "replay_window": "all",
            "warmup_bars": 60,
        },
        "validation": {
            "markets": [
                {
                    "market": {"symbol": symbol},
                    "folds": [{"selected_candidate": _candidate(0.5)}],
                }
                for symbol in SYMBOLS
            ]
        },
        "portfolio": {"summary": {"degraded": False}},
        "review_gate": {
            "disposition": "READY_FOR_SHADOW_REVIEW",
            "live_execution_allowed": False,
        },
    }


def _governance() -> dict:
    return {
        "schema_version": "mil3.promotion-governance.v1",
        "execution_mode": "PAPER_ONLY",
        "generated_at": START.isoformat(),
        "target_strategy": "AARS_DYNAMIC",
        "observed": {
            "mean_excess_return_vs_buy_hold": 0.03,
            "max_portfolio_drawdown": 0.08,
            "max_liquidation_risk": 0.02,
            "max_liquidation_events": 0,
        },
        "checks": [{"id": "ALL_EVIDENCE", "status": "PASS"}],
        "decision": {
            "disposition": "PROMOTION_CANDIDATE",
            "automatic_strategy_change_allowed": False,
            "live_execution_allowed": False,
        },
    }


def _seed(path: Path, *, acknowledge: bool = True) -> tuple[MarketStore, str, dict]:
    store = MarketStore(path)
    store.init_db()
    bars = 220
    last = START + timedelta(hours=bars - 1)
    for symbol_index, symbol in enumerate(SYMBOLS):
        candles = []
        for index in range(bars):
            center = 100.0 + symbol_index * 15 + index * 0.025
            wave = (index % 16 - 8) * 0.18
            close = center + wave
            candles.append(
                Candle(
                    symbol,
                    "1h",
                    START + timedelta(hours=index),
                    center,
                    max(center, close) + 0.4,
                    min(center, close) - 0.4,
                    close,
                    1000.0 + index,
                )
            )
        store.upsert_candles(candles, "test")
        store.upsert_funding_rates(
            [
                FundingRate(
                    symbol,
                    START + timedelta(hours=index),
                    0.0001,
                    candles[index].close,
                )
                for index in range(0, bars, 8)
            ],
            "test",
        )
    snapshot = _snapshot(last)
    snapshot_id = store.archive_shadow_daily_snapshot(snapshot, created_at=START)
    proposal = build_paper_configuration_proposal(
        _governance(), snapshot_id, snapshot, generated_at=START
    )
    proposal_id = store.archive_paper_configuration_proposal(proposal, created_at=START)
    if acknowledge:
        review = build_paper_proposal_review(
            proposal_id,
            proposal,
            disposition="ACKNOWLEDGED_FOR_PAPER_TRIAL",
            reviewer="local-owner",
            note="Run one isolated same-window paper trial.",
            reviewed_at=START,
        )
        store.archive_paper_proposal_review(review)
    envelope = store.get_paper_configuration_proposal(proposal_id)
    assert envelope is not None
    return store, proposal_id, envelope


def test_trial_replays_baseline_and_proposed_on_identical_hashed_inputs(tmp_path: Path):
    store, proposal_id, envelope = _seed(tmp_path / "market.sqlite")

    payload = build_paper_trial_result(store, envelope, generated_at=START)

    assert payload["schema_version"] == "mil3.paper-trial-result.v1"
    assert payload["proposal_id"] == proposal_id
    assert payload["lifecycle"]["state"] == "COMPLETED"
    assert payload["configuration"]["baseline"]["aars_max_abs_exposure"] == 1.0
    assert payload["configuration"]["proposed"]["aars_max_abs_exposure"] == 0.5
    assert len(payload["results"]["per_asset"]) == 2
    assert all(len(item["input_sha256"]) == 64 for item in payload["results"]["per_asset"])
    assert all(
        item["funding_coverage"]["status"] == "COMPLETE"
        for item in payload["results"]["per_asset"]
    )
    assert len(payload["input_evidence"]["combined_sha256"]) == 64
    assert "mean_total_return" in payload["results"]["delta_proposed_minus_baseline"]
    assert payload["authority"] == {
        "trial_application_allowed": False,
        "automatic_strategy_change_allowed": False,
        "live_execution_allowed": False,
    }
    json.dumps(payload, allow_nan=False)


def test_trial_fails_closed_without_acknowledgement_or_complete_funding(tmp_path: Path):
    store, _, pending = _seed(tmp_path / "pending.sqlite", acknowledge=False)
    with pytest.raises(ValueError, match="acknowledged"):
        build_paper_trial_result(store, pending)

    funded_store, _, envelope = _seed(tmp_path / "funding.sqlite")
    with funded_store.connect() as conn:
        conn.execute("DELETE FROM funding_rates")
    with pytest.raises(ValueError, match="funding history required"):
        build_paper_trial_result(funded_store, envelope)

    gapped_store, _, gapped_envelope = _seed(tmp_path / "gapped.sqlite")
    with gapped_store.connect() as conn:
        conn.execute(
            "DELETE FROM funding_rates WHERE symbol=? AND funding_time=?",
            ("BTCUSDT", (START + timedelta(hours=104)).isoformat()),
        )
    with pytest.raises(ValueError, match="status=GAPPED"):
        build_paper_trial_result(gapped_store, gapped_envelope)


def test_trial_stop_conditions_are_explicit(tmp_path: Path):
    store, _, envelope = _seed(tmp_path / "market.sqlite")
    payload = build_paper_trial_result(
        store,
        envelope,
        settings=PaperTrialSettings(stop_max_drawdown=0.0),
        generated_at=START,
    )

    assert payload["stop_condition"]["triggered"] is True
    assert "MAX_DRAWDOWN_LIMIT_EXCEEDED" in payload["stop_condition"]["reasons"]
    assert payload["review_gate"]["disposition"] == "STOP_TRIAL"
    assert payload["review_gate"]["trial_application_allowed"] is False


def test_trial_archive_is_idempotent_and_rejects_conflicting_result(tmp_path: Path):
    store, _, envelope = _seed(tmp_path / "market.sqlite")
    first = build_paper_trial_result(store, envelope, generated_at=START)
    later = build_paper_trial_result(
        store, envelope, generated_at=START + timedelta(hours=1)
    )

    first_id = store.archive_paper_trial_result(first)
    assert store.archive_paper_trial_result(later) == first_id
    assert len(store.list_paper_trial_results()) == 1

    unsafe_hash = json.loads(json.dumps(first))
    unsafe_hash["input_evidence"]["combined_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="does not match assets"):
        store.archive_paper_trial_result(unsafe_hash)

    changed = build_paper_trial_result(
        store,
        envelope,
        settings=PaperTrialSettings(fee_rate=0.001),
        generated_at=START,
    )
    with pytest.raises(ValueError, match="different trial result"):
        store.archive_paper_trial_result(changed)


def test_trial_api_is_read_only(tmp_path: Path):
    store, _, envelope = _seed(tmp_path / "market.sqlite")
    trial = build_paper_trial_result(store, envelope, generated_at=START)
    trial_id = store.archive_paper_trial_result(trial)
    service = DashboardService(store)
    handler_type = make_handler(service, tmp_path)
    handler = object.__new__(handler_type)

    handler.path = "/api/v1/paper-trials?strategy=AARS_DYNAMIC&limit=30"
    status, index = handler._api_payload()
    assert status == HTTPStatus.OK
    assert index["trials"][0]["trial_id"] == trial_id
    assert index["trial_application_allowed"] is False

    handler.path = f"/api/v1/paper-trials/{trial_id}"
    status, detail = handler._api_payload()
    assert status == HTTPStatus.OK
    assert detail["trial"]["proposal_id"] == envelope["proposal_id"]
    assert detail["live_execution_allowed"] is False
    assert len(store.list_paper_trial_results()) == 1

    handler.path = "/api/v1/paper-trials/missing"
    status, error = handler._api_payload()
    assert status == HTTPStatus.NOT_FOUND
    assert error == {"error": "paper trial not found"}


def test_trial_cli_is_the_explicit_local_write_path(tmp_path: Path):
    database = tmp_path / "market.sqlite"
    store, proposal_id, _ = _seed(database)
    runner = Path(__file__).parents[1] / "run_paper_trial.py"

    completed = subprocess.run(
        [
            sys.executable,
            str(runner),
            "--db",
            str(database),
            "--proposal-id",
            proposal_id,
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "execution_mode=PAPER_ONLY" in completed.stdout
    assert "trial_application_allowed=false" in completed.stdout
    assert "automatic_strategy_change_allowed=false" in completed.stdout
    assert "live_execution_allowed=false" in completed.stdout
    assert len(store.list_paper_trial_results()) == 1


def test_trial_ui_is_read_only_and_keeps_stop_and_authority_visible():
    ui_root = Path(__file__).parents[1] / "ui"
    html = (ui_root / "index.html").read_text(encoding="utf-8")
    javascript = (ui_root / "app.js").read_text(encoding="utf-8")
    css = (ui_root / "styles.css").read_text(encoding="utf-8")

    assert 'id="paper-trial-status"' in html
    assert 'id="paper-trial-comparison"' in html
    assert 'id="paper-trial-costs"' in html
    assert 'id="paper-trial-stop"' in html
    assert 'id="paper-trial-assets"' in html
    assert "TRIAL APPLICATION DISALLOWED" in html
    assert "LIVE EXECUTION DISALLOWED" in html
    assert "/api/v1/paper-trials?limit=30" in javascript
    assert "/api/v1/paper-trials/${encodeURIComponent(latest.trial_id)}" in javascript
    assert "paper trial did not preserve authority locks" in javascript
    assert "NO RESULT APPLIES A CONFIGURATION" in javascript
    assert '.paper-trial-card[data-status="STOP_TRIAL"]' in css
    assert '.paper-trial-card[data-status="CONTINUE_BASELINE"]' in css
    assert '.paper-trial-card[data-status="ELIGIBLE_FOR_EXTENDED_PAPER_OBSERVATION"]' in css
