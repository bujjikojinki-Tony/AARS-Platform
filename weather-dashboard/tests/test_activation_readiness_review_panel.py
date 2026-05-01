from __future__ import annotations

import weather_dashboard.ui.activation_readiness_review_panel as panel


def test_build_activation_readiness_review_panel_state_defaults() -> None:
    state = panel.build_activation_readiness_review_panel_state()

    assert state["summary"] is None
    assert state["reviews"] == []
    assert state["bundle"] is None
    assert state["raw_state"] == {}


def test_review_rows_map_records() -> None:
    rows = panel._review_rows(
        [
            {
                "activation_readiness_review_id": "arr_1",
                "market_id": "m1",
                "decision_id": "dec_1",
                "candidate_id": "cand_1",
                "approval_status": "APPROVED",
                "window_state": "OPEN",
                "review_status": "READY",
                "readiness_status": "READY",
                "recommendation": "READY_FOR_GOVERNED_REVIEW",
                "reviewed_at": "2026-05-01T00:00:00Z",
            }
        ]
    )

    assert rows[0]["market_id"] == "m1"
    assert rows[0]["decision_id"] == "dec_1"
    assert rows[0]["readiness_status"] == "READY"


def test_bundle_summary_includes_counts() -> None:
    text = panel._bundle_summary(
        {
            "market_id": "m1",
            "activation_readiness_reviews": [{}, {}],
        }
    )

    assert "m1" in text
    assert "2 activation readiness review rows" in text
