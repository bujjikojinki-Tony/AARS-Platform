from __future__ import annotations

import weather_dashboard.ui.market_snapshot_archive_panel as panel


def test_build_snapshot_archive_panel_state_defaults() -> None:
    state = panel.build_snapshot_archive_panel_state()

    assert state["summary"] is None
    assert state["recent_snapshots"] == []
    assert state["series"] is None
    assert state["warnings"] == []


def test_recent_rows_maps_archive_items() -> None:
    rows = panel._recent_rows(
        [
            {
                "snapshot_archive_id": "snap_1",
                "market_id": "m1",
                "source": "mock",
                "question": "Will it rain?",
                "yes_price": 0.6,
                "no_price": 0.4,
                "liquidity": 1000.0,
                "spread": 0.02,
                "archived_at": "2026-04-30T00:00:00Z",
                "market_source_mode": "MOCK_ONLY",
                "archive_reason": "PREVIEW_CAPTURE",
            }
        ]
    )

    assert rows[0]["market_id"] == "m1"
    assert rows[0]["archive_reason"] == "PREVIEW_CAPTURE"


def test_series_rows_maps_snapshot_series() -> None:
    rows = panel._series_rows(
        {
            "market_id": "m1",
            "count": 1,
            "first_archived_at": "2026-04-30T00:00:00Z",
            "last_archived_at": "2026-04-30T00:00:00Z",
            "snapshots": [
                {
                    "snapshot_archive_id": "snap_1",
                    "market_id": "m1",
                    "source": "mock",
                    "question": "Will it rain?",
                    "yes_price": 0.6,
                    "no_price": 0.4,
                    "liquidity": 1000.0,
                    "spread": 0.02,
                    "archived_at": "2026-04-30T00:00:00Z",
                    "market_source_mode": "MOCK_ONLY",
                    "archive_reason": "PREVIEW_CAPTURE",
                }
            ],
        }
    )

    assert rows[0]["source"] == "mock"
    assert rows[0]["spread"] == 0.02
