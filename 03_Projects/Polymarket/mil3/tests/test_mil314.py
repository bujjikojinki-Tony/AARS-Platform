from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from pathlib import Path

import pytest

from aars_market.api import make_handler
from aars_market.governance import PromotionPolicy, build_promotion_governance
from aars_market.service import DashboardService
from aars_market.storage import MarketStore


START = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _stability(
    snapshots: int = 30,
    *,
    excess_return: float = 0.03,
    drawdown: float = 0.10,
    liquidation_risk: float = 0.02,
    liquidation_events: int = 0,
    warnings: tuple[str, ...] = (),
    degraded: bool = False,
    ready: bool = True,
) -> dict:
    points = [
        {
            "snapshot_id": f"snapshot-{index:02d}",
            "as_of": (START + timedelta(days=index)).isoformat(),
            "validation_strategy": "AARS_DYNAMIC",
            "portfolio_strategy": "AARS_DYNAMIC",
            "selected_candidates": {
                "BTCUSDT": "AARS_DYNAMIC:exposure=0.5",
                "ETHUSDT": "AARS_DYNAMIC:exposure=0.5",
                "SOLUSDT": "AARS_DYNAMIC:exposure=0.5",
            },
            "warning_codes": list(warnings),
            "mean_validation_test_return": 0.08,
            "mean_validation_buy_hold_return": 0.08 - excess_return,
            "mean_validation_excess_return_vs_buy_hold": excess_return,
            "mean_selection_stability": 0.80,
            "portfolio": {
                "total_return": 0.12,
                "max_drawdown": drawdown,
                "final_net_exposure": 0.4,
                "final_gross_exposure": 0.4,
                "final_effective_leverage": 0.4,
                "min_margin_buffer_pct": 0.6,
                "max_liquidation_risk": liquidation_risk,
                "liquidation_events": liquidation_events,
                "degraded": degraded,
            },
            "review_disposition": (
                "READY_FOR_SHADOW_REVIEW" if ready else "DEFER"
            ),
        }
        for index in range(snapshots)
    ]
    transitions = [
        {
            "from_snapshot_id": points[index - 1]["snapshot_id"],
            "to_snapshot_id": points[index]["snapshot_id"],
            "candidate_changes": [],
            "warnings_added": [],
            "warnings_resolved": [],
            "review_transition": None,
        }
        for index in range(1, snapshots)
    ]
    return {
        "schema_version": "mil3.shadow-stability.v1",
        "execution_mode": "PAPER_ONLY",
        "generated_at": START.isoformat(),
        "snapshot_count": snapshots,
        "points": points,
        "transitions": transitions,
        "summary": {
            "current_disposition": points[-1]["review_disposition"] if points else None,
            "consecutive_ready_snapshots": snapshots if ready else 0,
            "parameter_change_events": 0,
            "recurring_warning_counts": {
                code: snapshots for code in warnings
            },
            "history_warnings": [] if snapshots >= 7 else ["INSUFFICIENT_DAILY_HISTORY"],
        },
        "review_gate": {
            "disposition": points[-1]["review_disposition"] if points else "DEFER",
            "live_execution_allowed": False,
        },
    }


def test_governance_marks_only_complete_clean_evidence_as_promotion_candidate():
    payload = build_promotion_governance(_stability(), generated_at=START)

    assert payload["schema_version"] == "mil3.promotion-governance.v1"
    assert payload["execution_mode"] == "PAPER_ONLY"
    assert payload["decision"]["disposition"] == "PROMOTION_CANDIDATE"
    assert payload["decision"]["blocking_checks"] == []
    assert payload["decision"]["rejection_checks"] == []
    assert payload["decision"]["automatic_strategy_change_allowed"] is False
    assert payload["decision"]["live_execution_allowed"] is False
    assert all(item["status"] == "PASS" for item in payload["checks"])
    json.dumps(payload, allow_nan=False)


def test_governance_continues_observation_for_insufficient_history_or_warnings():
    short = build_promotion_governance(_stability(5), generated_at=START)
    warned = build_promotion_governance(
        _stability(warnings=("FUNDING_HISTORY_FALLBACK",)), generated_at=START
    )

    assert short["decision"]["disposition"] == "CONTINUE_OBSERVATION"
    assert "MINIMUM_DAILY_HISTORY" in short["decision"]["blocking_checks"]
    assert warned["decision"]["disposition"] == "CONTINUE_OBSERVATION"
    assert "HIGH_RISK_WARNING_RECURRENCE" in warned["decision"]["blocking_checks"]
    assert warned["observed"]["high_risk_warning_recurrence"] == {
        "FUNDING_HISTORY_FALLBACK": 1.0
    }

    empty = build_promotion_governance(_stability(0), generated_at=START)
    statuses = {item["id"]: item["status"] for item in empty["checks"]}
    assert empty["decision"]["disposition"] == "CONTINUE_OBSERVATION"
    assert statuses["PARAMETER_CHANGE_RATE"] == "BLOCK"
    assert statuses["HIGH_RISK_WARNING_RECURRENCE"] == "BLOCK"


def test_governance_counts_only_explicitly_eligible_closed_evidence():
    stability = _stability()
    stability["promotion_eligible_points"] = stability["points"][-2:]

    payload = build_promotion_governance(stability, generated_at=START)

    assert payload["evidence_window"] == {
        "available_snapshots": 2,
        "archived_snapshots": 30,
        "excluded_ineligible_snapshots": 28,
        "evaluated_snapshots": 2,
        "first_as_of": stability["points"][-2]["as_of"],
        "latest_as_of": stability["points"][-1]["as_of"],
    }
    assert payload["decision"]["disposition"] == "CONTINUE_OBSERVATION"
    assert "MINIMUM_DAILY_HISTORY" in payload["decision"]["blocking_checks"]


@pytest.mark.parametrize(
    ("kwargs", "check_id"),
    [
        ({"excess_return": -0.08}, "EXCESS_RETURN_VS_BUY_HOLD"),
        ({"drawdown": 0.40}, "MAX_PORTFOLIO_DRAWDOWN"),
        ({"liquidation_risk": 0.30}, "MAX_LIQUIDATION_RISK"),
        ({"liquidation_events": 1}, "LIQUIDATION_EVENTS"),
    ],
)
def test_governance_rejects_material_performance_or_risk_breaches(kwargs, check_id):
    payload = build_promotion_governance(_stability(**kwargs), generated_at=START)

    assert payload["decision"]["disposition"] == "REJECT_PROMOTION"
    assert check_id in payload["decision"]["rejection_checks"]


def test_governance_rejects_unsafe_source_evidence_and_bad_policy():
    unsafe = _stability()
    unsafe["review_gate"]["live_execution_allowed"] = True
    with pytest.raises(ValueError, match="disallow live execution"):
        build_promotion_governance(unsafe)
    with pytest.raises(ValueError, match="reject drawdown"):
        PromotionPolicy(
            max_portfolio_drawdown=0.30,
            reject_drawdown_at_or_above=0.20,
        )
    with pytest.raises(ValueError, match="evaluation window"):
        PromotionPolicy(evaluation_window_snapshots=10, min_snapshots=30)


def test_promotion_governance_api_is_read_only(tmp_path: Path):
    store = MarketStore(tmp_path / "market.sqlite")
    store.init_db()
    service = DashboardService(store)
    service.shadow_stability = lambda **_kwargs: _stability()  # type: ignore[method-assign]
    handler_type = make_handler(service, tmp_path)
    handler = object.__new__(handler_type)
    handler.path = "/api/v1/promotion-governance?strategy=AARS_DYNAMIC&limit=30"

    status, payload = handler._api_payload()

    assert status == HTTPStatus.OK
    assert payload["decision"]["disposition"] == "PROMOTION_CANDIDATE"
    assert payload["review_gate"]["live_execution_allowed"] is False
    assert store.list_shadow_daily_snapshots() == []


def test_promotion_governance_ui_exposes_advisory_decision_and_locks():
    ui_root = Path(__file__).parents[1] / "ui"
    html = (ui_root / "index.html").read_text(encoding="utf-8")
    javascript = (ui_root / "app.js").read_text(encoding="utf-8")
    css = (ui_root / "styles.css").read_text(encoding="utf-8")

    assert 'id="promotion-disposition"' in html
    assert 'id="promotion-checks"' in html
    assert 'id="promotion-policy-list"' in html
    assert "AUTOMATIC STRATEGY CHANGE LOCKED" in html
    assert "LIVE EXECUTION DISALLOWED" in html
    assert "/api/v1/promotion-governance?limit=90" in javascript
    assert "automatic_strategy_change_allowed !== false" in javascript
    assert "governance evidence did not deny live execution" in javascript
    assert '.promotion-card[data-status="PROMOTION_CANDIDATE"]' in css
    assert '.promotion-card[data-status="REJECT_PROMOTION"]' in css
    assert '.promotion-check[data-status="REJECT"]' in css
