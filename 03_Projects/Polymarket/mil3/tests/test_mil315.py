from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from pathlib import Path

import pytest

from aars_market.api import make_handler
from aars_market.proposal import (
    build_paper_configuration_proposal,
    build_paper_proposal_review,
)
from aars_market.service import DashboardService
from aars_market.storage import MarketStore


START = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _candidate(exposure: float = 0.5) -> dict:
    return {
        "candidate_id": f"AARS_DYNAMIC:exposure={exposure:g}",
        "target_strategy": "AARS_DYNAMIC",
        "aars_max_abs_exposure": exposure,
        "futures_leverage": 10.0,
        "grid_spacing_pct": 0.01,
        "grid_levels": 5,
        "tactical_hedge": True,
    }


def _snapshot(exposures: tuple[float, ...] = (0.5, 0.5, 0.75)) -> dict:
    symbols = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
    return {
        "schema_version": "mil3.shadow-daily.v1",
        "execution_mode": "PAPER_ONLY",
        "generated_at": START.isoformat(),
        "as_of": START.isoformat(),
        "symbols": list(symbols),
        "configuration": {
            "validation_strategy": "AARS_DYNAMIC",
            "portfolio_strategy": "AARS_DYNAMIC",
        },
        "validation": {
            "markets": [
                {
                    "market": {"symbol": symbol},
                    "folds": [{"selected_candidate": _candidate(exposure)}],
                }
                for symbol, exposure in zip(symbols, exposures)
            ]
        },
        "portfolio": {"summary": {"degraded": False}},
        "review_gate": {
            "disposition": "READY_FOR_SHADOW_REVIEW",
            "live_execution_allowed": False,
        },
    }


def _governance(disposition: str = "PROMOTION_CANDIDATE") -> dict:
    return {
        "schema_version": "mil3.promotion-governance.v1",
        "execution_mode": "PAPER_ONLY",
        "generated_at": START.isoformat(),
        "target_strategy": "AARS_DYNAMIC",
        "observed": {
            "mean_excess_return_vs_buy_hold": 0.04,
            "max_portfolio_drawdown": 0.12,
            "max_liquidation_risk": 0.03,
            "max_liquidation_events": 0,
        },
        "checks": [{"id": "ALL_EVIDENCE", "status": "PASS"}],
        "decision": {
            "disposition": disposition,
            "automatic_strategy_change_allowed": False,
            "live_execution_allowed": False,
        },
    }


def _archive_source(store: MarketStore, snapshot: dict | None = None) -> tuple[str, dict]:
    payload = snapshot or _snapshot()
    snapshot_id = store.archive_shadow_daily_snapshot(payload, created_at=START)
    return snapshot_id, payload


def test_proposal_is_deterministic_advisory_and_uses_cross_asset_mode():
    payload = build_paper_configuration_proposal(
        _governance(), "snapshot-1", _snapshot(), generated_at=START
    )

    assert payload["schema_version"] == "mil3.paper-configuration-proposal.v1"
    assert payload["status"] == "PENDING_HUMAN_REVIEW"
    assert payload["selection"]["selected_candidate_id"] == "AARS_DYNAMIC:exposure=0.5"
    assert payload["selection"]["selection_count"] == 2
    assert payload["parameter_changes"] == [
        {
            "parameter": "aars_max_abs_exposure",
            "before": 1.0,
            "after": 0.5,
            "absolute_delta": -0.5,
            "relative_delta": -0.5,
        }
    ]
    assert payload["expected_risk_impact"]["assessment"] == "NOT_FORECAST"
    assert payload["authority"] == {
        "proposal_application_allowed": False,
        "automatic_strategy_change_allowed": False,
        "live_execution_allowed": False,
    }
    json.dumps(payload, allow_nan=False)


def test_proposal_fails_closed_without_candidate_or_safe_authority():
    with pytest.raises(ValueError, match="PROMOTION_CANDIDATE"):
        build_paper_configuration_proposal(
            _governance("CONTINUE_OBSERVATION"), "snapshot-1", _snapshot()
        )
    unsafe = _governance()
    unsafe["decision"]["automatic_strategy_change_allowed"] = True
    with pytest.raises(ValueError, match="lock automatic"):
        build_paper_configuration_proposal(unsafe, "snapshot-1", _snapshot())
    with pytest.raises(ValueError, match="does not change"):
        build_paper_configuration_proposal(
            _governance(), "snapshot-1", _snapshot((1.0, 1.0, 1.0))
        )
    malformed = _snapshot()
    malformed["validation"]["markets"][0]["folds"][0]["selected_candidate"][
        "candidate_id"
    ] = "AARS_DYNAMIC:exposure=10"
    with pytest.raises(ValueError, match="candidate id"):
        build_paper_configuration_proposal(
            _governance(), "snapshot-1", malformed
        )


def test_proposal_and_terminal_review_archives_are_immutable_and_idempotent(
    tmp_path: Path,
):
    store = MarketStore(tmp_path / "market.sqlite")
    store.init_db()
    snapshot_id, snapshot = _archive_source(store)
    proposal = build_paper_configuration_proposal(
        _governance(), snapshot_id, snapshot, generated_at=START
    )

    wrong_target = dict(proposal)
    wrong_target["target_strategy"] = "SPOT_GRID"
    with pytest.raises(ValueError, match="differs from its source"):
        store.archive_paper_configuration_proposal(wrong_target, created_at=START)

    first = store.archive_paper_configuration_proposal(proposal, created_at=START)
    second = store.archive_paper_configuration_proposal(proposal, created_at=START)
    assert first == second
    assert len(store.list_paper_configuration_proposals()) == 1

    review = build_paper_proposal_review(
        first,
        proposal,
        disposition="ACKNOWLEDGED_FOR_PAPER_TRIAL",
        reviewer="local-owner",
        note="Proceed only through a separately configured paper trial.",
        reviewed_at=START,
    )
    review_id = store.archive_paper_proposal_review(review)
    unsafe_review = dict(review)
    unsafe_review["disposition"] = "APPLIED"
    with pytest.raises(ValueError, match="unsupported"):
        store.archive_paper_proposal_review(unsafe_review)
    repeated = dict(review)
    repeated["reviewed_at"] = (START + timedelta(hours=1)).isoformat()
    assert store.archive_paper_proposal_review(repeated) == review_id
    envelope = store.get_paper_configuration_proposal(first)
    assert envelope is not None
    assert envelope["status"] == "ACKNOWLEDGED_FOR_PAPER_TRIAL"
    assert envelope["proposal_application_allowed"] is False
    assert envelope["review"]["acknowledgement_applies_parameters"] is False

    conflicting = build_paper_proposal_review(
        first,
        proposal,
        disposition="DECLINED",
        reviewer="local-owner",
        note="Declined after review.",
        reviewed_at=START,
    )
    with pytest.raises(ValueError, match="terminal review"):
        store.archive_paper_proposal_review(conflicting)


def test_paper_proposal_api_is_read_only(tmp_path: Path):
    store = MarketStore(tmp_path / "market.sqlite")
    store.init_db()
    snapshot_id, snapshot = _archive_source(store)
    proposal = build_paper_configuration_proposal(
        _governance(), snapshot_id, snapshot, generated_at=START
    )
    proposal_id = store.archive_paper_configuration_proposal(proposal, created_at=START)
    service = DashboardService(store)
    handler_type = make_handler(service, tmp_path)
    handler = object.__new__(handler_type)

    handler.path = "/api/v1/paper-proposals?strategy=AARS_DYNAMIC&limit=30"
    status, index = handler._api_payload()
    assert status == HTTPStatus.OK
    assert index["proposals"][0]["proposal_id"] == proposal_id
    assert index["proposal_application_allowed"] is False

    handler.path = f"/api/v1/paper-proposals/{proposal_id}"
    status, detail = handler._api_payload()
    assert status == HTTPStatus.OK
    assert detail["status"] == "PENDING_HUMAN_REVIEW"
    assert detail["live_execution_allowed"] is False
    assert len(store.list_paper_configuration_proposals()) == 1

    handler.path = "/api/v1/paper-proposals/missing"
    status, error = handler._api_payload()
    assert status == HTTPStatus.NOT_FOUND
    assert error == {"error": "paper proposal not found"}


def test_review_cli_is_explicit_local_write_path(tmp_path: Path):
    database = tmp_path / "market.sqlite"
    store = MarketStore(database)
    store.init_db()
    snapshot_id, snapshot = _archive_source(store)
    proposal = build_paper_configuration_proposal(
        _governance(), snapshot_id, snapshot, generated_at=START
    )
    proposal_id = store.archive_paper_configuration_proposal(proposal, created_at=START)
    runner = Path(__file__).parents[1] / "run_paper_review.py"

    completed = subprocess.run(
        [
            sys.executable,
            str(runner),
            "--db",
            str(database),
            "--proposal-id",
            proposal_id,
            "--disposition",
            "DECLINED",
            "--reviewer",
            "local-owner",
            "--note",
            "Keep observing before any paper trial.",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "execution_mode=PAPER_ONLY" in completed.stdout
    assert "acknowledgement_applies_parameters=false" in completed.stdout
    assert "live_execution_allowed=false" in completed.stdout
    assert store.get_paper_configuration_proposal(proposal_id)["status"] == "DECLINED"


def test_paper_proposal_ui_is_read_only_and_keeps_authority_visible():
    ui_root = Path(__file__).parents[1] / "ui"
    html = (ui_root / "index.html").read_text(encoding="utf-8")
    javascript = (ui_root / "app.js").read_text(encoding="utf-8")
    css = (ui_root / "styles.css").read_text(encoding="utf-8")

    assert 'id="paper-proposal-status"' in html
    assert 'id="paper-proposal-changes"' in html
    assert 'id="paper-proposal-risk"' in html
    assert 'id="paper-proposal-review"' in html
    assert "ACKNOWLEDGEMENT DOES NOT APPLY PARAMETERS" in html
    assert "AUTOMATIC STRATEGY CHANGE LOCKED" in html
    assert "LIVE EXECUTION DISALLOWED" in html
    assert "/api/v1/paper-proposals?limit=30" in javascript
    assert "/api/v1/paper-proposals/${encodeURIComponent(latest.proposal_id)}" in javascript
    assert "paper proposal did not preserve authority locks" in javascript
    assert "THIS SCREEN HAS NO APPROVE OR APPLY CONTROL" in javascript
    assert '.paper-proposal-card[data-status="ACKNOWLEDGED_FOR_PAPER_TRIAL"]' in css
    assert '.paper-proposal-card[data-status="DECLINED"]' in css
