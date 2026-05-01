from __future__ import annotations

import weather_dashboard.ui.approval_window_review_panel as panel


def test_build_approval_window_review_panel_state_defaults() -> None:
    state = panel.build_approval_window_review_panel_state()

    assert state["summary"] is None
    assert state["reviews"] == []
    assert state["bundle"] is None
    assert state["raw_state"] == {}


def test_review_rows_map_records() -> None:
    rows = panel._review_rows(
        [
            {
                "approval_window_review_id": "awr_1",
                "market_id": "m1",
                "decision_id": "dec_1",
                "candidate_id": "cand_1",
                "approval_status": "PENDING",
                "approval_window_valid": True,
                "approval_valid_until": "2026-05-10T00:00:00Z",
                "review_status": "READY",
                "window_state": "OPEN",
                "recommendation": "REVIEW_WINDOW",
                "reviewed_at": "2026-05-01T00:00:00Z",
            }
        ]
    )

    assert rows[0]["market_id"] == "m1"
    assert rows[0]["decision_id"] == "dec_1"
    assert rows[0]["window_state"] == "OPEN"


def test_bundle_summary_includes_counts() -> None:
    text = panel._bundle_summary(
        {
            "market_id": "m1",
            "approval_window_reviews": [{}, {}],
        }
    )

    assert "m1" in text
    assert "2 approval window review rows" in text
