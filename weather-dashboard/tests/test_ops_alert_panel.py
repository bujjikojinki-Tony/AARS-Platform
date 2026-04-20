from weather_dashboard.ui.ops_alert_panel import build_ops_alert_overview


def test_ops_alert_overview_counts_alerts_notifications_and_deliveries():
    overview = build_ops_alert_overview(
        alert_events=[
            {
                "event_at": "2026-04-19T12:00:00+00:00",
                "automation_signal": "red",
                "market_id": "m-1",
                "primary_block_reason": "stale_worker",
                "recommended_operator_action": "refresh_pipeline_inputs",
                "gate_source": "api",
                "text": "first alert",
            },
            {
                "event_at": "2026-04-19T12:05:00+00:00",
                "automation_signal": "amber",
                "market_id": "m-2",
                "primary_block_reason": "resolver_not_matched",
                "recommended_operator_action": "review_resolver_contract",
                "gate_source": "unified_fallback",
                "text": "second alert",
            },
        ],
        notification_events=[
            {
                "notification_id": "ops_1",
                "status": "pending",
                "delivery_state": "pending",
                "created_at": "2026-04-19T12:00:10+00:00",
                "channel": "telegram_ops_bridge",
                "dedupe_key": "dedupe-1",
            },
            {
                "notification_id": "ops_2",
                "status": "acked",
                "delivery_state": "acked",
                "created_at": "2026-04-19T12:05:10+00:00",
                "channel": "telegram_ops_bridge",
                "dedupe_key": "dedupe-2",
            },
        ],
        delivery_events=[
            {
                "event_type": "notification_sent",
                "event_at": "2026-04-19T12:00:20+00:00",
                "notification_id": "ops_1",
            },
            {
                "event_type": "notification_acked",
                "event_at": "2026-04-19T12:05:20+00:00",
                "notification_id": "ops_2",
            },
        ],
    )

    assert overview["schema_version"] == "dashboard_ops_overview.v1"
    assert overview["alert_count"] == 2
    assert overview["notification_count"] == 2
    assert overview["delivery_event_count"] == 2
    assert overview["signal_counts"]["red"] == 1
    assert overview["signal_counts"]["amber"] == 1
    assert overview["delivery_state_counts"]["pending"] == 1
    assert overview["delivery_state_counts"]["acked"] == 1
    assert overview["latest_alert"]["market_id"] == "m-2"
    assert overview["latest_notification"]["notification_id"] == "ops_2"
