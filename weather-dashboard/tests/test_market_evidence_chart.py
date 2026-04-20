import pandas as pd

from weather_dashboard.ui.market_evidence_chart import build_market_evidence_context


def test_market_evidence_context_builds_chart_frames_and_markers() -> None:
    samples = pd.DataFrame(
        [
            {
                "market_id": "m1",
                "timestamp": "2026-04-18T00:00:00+00:00",
                "market_probability": 0.52,
                "yes_price": 0.53,
                "model_probability": 0.61,
                "fair_value": 0.6,
                "model_value": 28.4,
                "official_value": None,
                "comparison_status": "aligned",
                "action_hint": "watch",
                "is_labeled": False,
            },
            {
                "market_id": "m1",
                "timestamp": "2026-04-18T01:00:00+00:00",
                "market_probability": 0.55,
                "yes_price": 0.56,
                "model_probability": 0.63,
                "fair_value": 0.62,
                "model_value": 28.8,
                "official_value": 29.0,
                "comparison_status": "diverged",
                "action_hint": "review",
                "is_labeled": True,
            },
            {
                "market_id": "m2",
                "timestamp": "2026-04-18T01:00:00+00:00",
                "market_probability": 0.2,
                "model_probability": 0.3,
            },
        ]
    )
    audit_events = [
        {
            "market_id": "m1",
            "created_at": "2026-04-18T01:05:00+00:00",
            "event_type": "manual_advisory_signal_created",
            "payload": {
                "decision": "approve_small",
                "gate_status": "READY",
                "comparison_status": "diverged",
                "manual_trade_ticket": {"price": 0.56, "size": 10.0},
            },
        },
        {
            "market_id": "m2",
            "created_at": "2026-04-18T01:06:00+00:00",
            "event_type": "operator_acknowledged_manual_advisory",
            "payload": {"manual_trade_ticket": {"price": 0.2, "size": 10.0}},
        },
    ]

    context = build_market_evidence_context(samples, "m1", audit_events)

    assert context["sample_count"] == 2
    assert context["labeled_rows"] == 1
    assert list(context["price_chart_df"].columns) == [
        "market_probability",
        "yes_price",
        "model_probability",
        "fair_value",
    ]
    assert list(context["value_chart_df"].columns) == ["model_value", "official_value"]
    assert context["latest_market_probability"] == 0.55
    assert context["latest_official_value"] == 29.0
    assert len(context["approval_markers"]) == 1
    assert context["approval_markers"][0]["event_type"] == "manual_advisory_signal_created"


def test_market_evidence_context_returns_empty_when_market_has_no_rows() -> None:
    samples = pd.DataFrame(
        [
            {
                "market_id": "m2",
                "timestamp": "2026-04-18T00:00:00+00:00",
                "market_probability": 0.22,
            }
        ]
    )

    context = build_market_evidence_context(samples, "m1", [])

    assert context["sample_count"] == 0
    assert context["price_chart_df"].empty
    assert context["value_chart_df"].empty
