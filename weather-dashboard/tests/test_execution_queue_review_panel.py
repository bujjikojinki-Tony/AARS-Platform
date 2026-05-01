from __future__ import annotations

import weather_dashboard.ui.execution_queue_review_panel as panel


def test_build_execution_queue_review_panel_state_defaults() -> None:
    state = panel.build_execution_queue_review_panel_state()

    assert state["summary"] is None
    assert state["reviews"] == []
    assert state["bundle"] is None
    assert state["raw_state"] == {}


def test_review_rows_map_records() -> None:
    rows = panel._review_rows(
        [
            {
                "execution_queue_review_id": "eqr_1",
                "market_id": "m1",
                "decision_id": "dec_1",
                "candidate_id": "cand_1",
                "execution_mode": "OBSERVE_ONLY",
                "execution_status": "QUEUED",
                "review_status": "READY",
                "approval_status": "PENDING",
                "gate_status": "ALLOW",
                "recommendation": "REVIEW_EXECUTION",
                "reviewed_at": "2026-05-01T00:00:00Z",
            }
        ]
    )

    assert rows[0]["market_id"] == "m1"
    assert rows[0]["decision_id"] == "dec_1"
    assert rows[0]["gate_status"] == "ALLOW"


def test_bundle_summary_includes_counts() -> None:
    text = panel._bundle_summary(
        {
            "market_id": "m1",
            "execution_queue_reviews": [{}, {}],
        }
    )

    assert "m1" in text
    assert "2 execution queue review rows" in text
