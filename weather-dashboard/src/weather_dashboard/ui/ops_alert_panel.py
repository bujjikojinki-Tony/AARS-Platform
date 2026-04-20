from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from html import escape

import streamlit as st

from weather_dashboard.ui.compact_panel import fmt_value, render_kv_section, render_panel_title, sanitize_text


def build_ops_alert_overview(
    *,
    alert_events: list[dict] | None = None,
    notification_events: list[dict] | None = None,
    delivery_events: list[dict] | None = None,
) -> dict:
    alerts = [event for event in (alert_events or []) if isinstance(event, dict)]
    notifications = [item for item in (notification_events or []) if isinstance(item, dict)]
    deliveries = [item for item in (delivery_events or []) if isinstance(item, dict)]

    alert_counter = Counter(str(event.get("automation_signal") or "unknown").lower() for event in alerts)
    delivery_counter = Counter(
        str(item.get("delivery_state") or item.get("status") or "unknown").lower()
        for item in notifications
    )

    latest_alert = _latest_record(alerts, candidates=("event_at", "created_at"))
    latest_notification = _latest_record(notifications, candidates=("created_at", "sent_at", "acked_at"))
    latest_delivery = _latest_record(deliveries, candidates=("event_at",))

    return {
        "schema_version": "dashboard_ops_overview.v1",
        "alert_count": len(alerts),
        "notification_count": len(notifications),
        "delivery_event_count": len(deliveries),
        "signal_counts": dict(alert_counter),
        "delivery_state_counts": dict(delivery_counter),
        "latest_alert": latest_alert,
        "latest_notification": latest_notification,
        "latest_delivery": latest_delivery,
        "latest_alert_text": str(latest_alert.get("text") or "-") if latest_alert else "-",
        "latest_notification_text": str(latest_notification.get("text") or "-") if latest_notification else "-",
    }


def render_ops_alert_panel(
    *,
    alert_events: list[dict] | None = None,
    notification_events: list[dict] | None = None,
    delivery_events: list[dict] | None = None,
) -> None:
    overview = build_ops_alert_overview(
        alert_events=alert_events,
        notification_events=notification_events,
        delivery_events=delivery_events,
    )
    render_panel_title("Ops Alert / Queue", "Read-only operator summary for runtime alerts and queue state.")

    metric_cols = st.columns(3)
    metric_cols[0].metric("Alerts", overview["alert_count"])
    metric_cols[1].metric("Notifications", overview["notification_count"])
    metric_cols[2].metric("Delivery Events", overview["delivery_event_count"])

    render_kv_section(
        "Signal Distribution",
        [
            ("Green", overview["signal_counts"].get("green", 0)),
            ("Amber", overview["signal_counts"].get("amber", 0)),
            ("Red", overview["signal_counts"].get("red", 0)),
        ],
    )
    render_kv_section(
        "Queue Distribution",
        [
            ("Pending", overview["delivery_state_counts"].get("pending", 0)),
            ("Sent", overview["delivery_state_counts"].get("sent", 0)),
            ("Acked", overview["delivery_state_counts"].get("acked", 0)),
            ("Suppressed", overview["delivery_state_counts"].get("suppressed", 0)),
        ],
    )

    latest_alert = overview.get("latest_alert") or {}
    latest_notification = overview.get("latest_notification") or {}
    latest_delivery = overview.get("latest_delivery") or {}

    left, right = st.columns([1, 1])
    with left:
        render_kv_section(
            "Latest Alert",
            [
                ("Market", latest_alert.get("market_id")),
                ("Reason", latest_alert.get("primary_block_reason")),
                ("Action", latest_alert.get("recommended_operator_action")),
                ("Cooldown", latest_alert.get("cooldown_until")),
                ("Gate Source", latest_alert.get("gate_source")),
            ],
            metric_label="Signal",
            metric_value=latest_alert.get("automation_signal"),
        )
        if latest_alert:
            st.caption(escape(fmt_value(latest_alert.get("text"))))
    with right:
        render_kv_section(
            "Latest Notification",
            [
                ("Notification", latest_notification.get("notification_id")),
                ("Status", latest_notification.get("status") or latest_notification.get("delivery_state")),
                ("Created", latest_notification.get("created_at")),
                ("Channel", latest_notification.get("channel")),
                ("Dedup", latest_notification.get("dedupe_key")),
            ],
        )
        if latest_delivery:
            render_kv_section(
                "Latest Delivery Event",
                [
                    ("Type", latest_delivery.get("event_type")),
                    ("Event At", latest_delivery.get("event_at")),
                    ("Notification", latest_delivery.get("notification_id")),
                ],
            )


def _latest_record(records: list[dict], *, candidates: tuple[str, ...]) -> dict:
    if not records:
        return {}

    def sort_key(record: dict) -> datetime:
        for field in candidates:
            parsed = _parse_dt(record.get(field))
            if parsed is not None:
                return parsed
        return datetime.min.replace(tzinfo=timezone.utc)

    ordered = sorted(records, key=sort_key, reverse=True)
    return ordered[0] if ordered else {}


def _parse_dt(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)
