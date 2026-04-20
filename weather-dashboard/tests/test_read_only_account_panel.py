from weather_dashboard.ui.read_only_account_panel import build_read_only_account_summary


def test_build_read_only_account_summary_computes_selected_market_exposure() -> None:
    summary = build_read_only_account_summary(
        {
            "updated_at": "2026-04-18T00:00:00+00:00",
            "source": "sample_account_snapshot",
            "account_id": "acct_1",
            "balance": {
                "available_balance": 100,
                "total_balance": 125,
                "currency": "USDC",
                "manual_order_only": True,
            },
            "positions": [
                {"market_id": "m1", "size": 100, "current_price": 0.4},
                {"market_id": "m2", "notional": 12.5},
            ],
            "open_orders": [
                {"market_id": "m1", "remaining_size": 10, "price": 0.5},
                {"market_id": "m3", "notional": 7},
            ],
        },
        "m1",
        {
            "checks": [
                {
                    "name": "exposure_limits",
                    "status": "passed",
                    "details": {
                        "max_notional_per_market": 100,
                        "max_total_notional": 500,
                    },
                }
            ]
        },
    )

    assert summary["available"] is True
    assert summary["manual_order_only"] is True
    assert summary["position_notional"] == 52.5
    assert summary["open_order_notional"] == 12.0
    assert summary["total_notional"] == 64.5
    assert summary["market_position_notional"] == 40.0
    assert summary["market_open_order_notional"] == 5.0
    assert summary["market_notional"] == 45.0
    assert summary["market_position_count"] == 1
    assert summary["market_open_order_count"] == 1
    assert summary["market_limit_usage"] == 0.45
    assert summary["total_limit_usage"] == 0.129
    assert summary["exposure_limit_status"] == "within_limit"


def test_build_read_only_account_summary_missing_snapshot() -> None:
    summary = build_read_only_account_summary(None, "m1")

    assert summary["available"] is False
    assert summary["manual_order_only"] is True
    assert summary["total_notional"] == 0.0


def test_build_read_only_account_summary_flags_near_limit() -> None:
    summary = build_read_only_account_summary(
        {
            "balance": {"currency": "USDC", "manual_order_only": True},
            "positions": [{"market_id": "m1", "notional": 85}],
            "open_orders": [],
        },
        "m1",
        {
            "checks": [
                {
                    "name": "exposure_limits",
                    "details": {
                        "max_notional_per_market": 100,
                        "max_total_notional": 500,
                    },
                }
            ]
        },
    )

    assert summary["market_limit_usage"] == 0.85
    assert summary["exposure_limit_status"] == "near_limit"


def test_build_read_only_account_summary_flags_over_limit() -> None:
    summary = build_read_only_account_summary(
        {
            "balance": {"currency": "USDC", "manual_order_only": True},
            "positions": [{"market_id": "m1", "notional": 120}],
            "open_orders": [],
        },
        "m1",
        {
            "checks": [
                {
                    "name": "exposure_limits",
                    "details": {
                        "max_notional_per_market": 100,
                        "max_total_notional": 500,
                    },
                }
            ]
        },
    )

    assert summary["market_limit_usage"] == 1.2
    assert summary["exposure_limit_status"] == "over_limit"
