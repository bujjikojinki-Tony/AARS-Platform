from weather_dashboard.ui.manual_advisory_reconciliation_panel import (
    build_manual_advisory_reconciliation_summary,
)


def test_manual_advisory_reconciliation_summary_missing():
    summary = build_manual_advisory_reconciliation_summary(None)

    assert summary["available"] is False
    assert summary["overall_status"] == "missing"


def test_manual_advisory_reconciliation_summary_uses_latest_item():
    summary = build_manual_advisory_reconciliation_summary(
        {
            "overall_status": "needs_review",
            "fill_count": 2,
            "reconciled_count": 1,
            "needs_review_count": 1,
            "unmatched_count": 0,
            "items": [
                {"market_id": "market_1", "review_reason": None},
                {
                    "market_id": "market_2",
                    "review_reason": "position_snapshot_does_not_cover_fill_notional",
                },
            ],
        }
    )

    assert summary["available"] is True
    assert summary["overall_status"] == "needs_review"
    assert summary["latest_market_id"] == "market_2"
    assert summary["latest_review_reason"] == "position_snapshot_does_not_cover_fill_notional"
