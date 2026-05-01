from __future__ import annotations

import weather_dashboard.ui.command_review_panel as panel


def test_build_command_review_panel_state_defaults() -> None:
    state = panel.build_command_review_panel_state()

    assert state["summary"] is None
    assert state["reviews"] == []
    assert state["bundle"] is None
    assert state["raw_state"] == {}


def test_review_rows_map_records() -> None:
    rows = panel._review_rows(
        [
            {
                "command_review_id": "crv_1",
                "market_id": "m1",
                "command_name": "/review",
                "source_page": "command",
                "review_status": "READY",
                "approval_status": "PENDING",
                "recommendation": "REVIEW_EVIDENCE",
                "gate_status": "WARN",
                "execution_mode": "OBSERVE_ONLY",
                "risk_status": "WARN",
                "reviewed_at": "2026-05-01T00:00:00Z",
            }
        ]
    )

    assert rows[0]["market_id"] == "m1"
    assert rows[0]["command_name"] == "/review"
    assert rows[0]["gate_status"] == "WARN"


def test_bundle_summary_includes_counts() -> None:
    text = panel._bundle_summary(
        {
            "market_id": "m1",
            "command_reviews": [{}, {}],
        }
    )

    assert "m1" in text
    assert "2 command review rows" in text
