import asyncio
from types import SimpleNamespace

from weather_telegram_console.bot.handlers.monitoring import monitoring_handler


class FakeMessage:
    def __init__(self) -> None:
        self.text: str | None = None
        self.parse_mode: str | None = None

    async def reply_text(self, text: str, parse_mode: str | None = None) -> None:
        self.text = text
        self.parse_mode = parse_mode


class FakeUpdate:
    def __init__(self) -> None:
        self.message = FakeMessage()


def test_monitoring_handler(monkeypatch) -> None:
    monkeypatch.setattr(
        "weather_telegram_console.bot.handlers.monitoring.MonitoringAPI.load_latest_monitoring_signals",
        lambda self: {
            "alert_count": 1,
            "family_scan_count": 1,
            "anomaly_event_count": 1,
            "latest_alert": {
                "market_id": "693874",
                "market_family": "sea_ice_extent",
                "severity": "amber",
                "primary_reason": "strong_divergence_or_reaction_gap",
                "recommended_operator_action": "review_market_now",
                "generated_at": "2026-04-21T03:33:44+00:00",
            },
            "latest_family_scan_report": {
                "family_count": 1,
                "market_count": 1,
                "generated_at": "2026-04-21T03:33:44+00:00",
                "family_summaries": [
                    {"market_family": "sea_ice_extent", "max_intervention_like_score": 0.37}
                ],
            },
            "latest_anomaly_event": {
                "market_id": "693874",
                "market_family": "sea_ice_extent",
                "anomaly_score": 0.41,
                "intervention_like_score": 0.37,
                "primary_reason": "edge_dislocation",
                "generated_at": "2026-04-21T03:33:44+00:00",
            },
            "runtime_block": {
                "overall_status": "blocked",
                "gate_status": "blocked",
                "execution_status": "blocked",
                "ready_for_live": False,
                "can_execute": False,
                "primary_block_reason": "comparison_not_actionable",
                "recommended_operator_action": "hold_execution_and_review",
                "block_reason_count": 4,
            },
        },
    )

    update = FakeUpdate()
    context = SimpleNamespace()
    asyncio.run(monitoring_handler(update, context))

    assert update.message.parse_mode == "Markdown"
    assert update.message.text is not None
    assert "AARS Monitoring Signals" in update.message.text
    assert "Gate / Runtime Block" in update.message.text
