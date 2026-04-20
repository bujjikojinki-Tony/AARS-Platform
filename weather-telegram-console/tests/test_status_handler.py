import asyncio

from weather_telegram_console.bot.handlers.status import status_handler


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


def test_status_handler(monkeypatch) -> None:
    monkeypatch.setattr(
        "weather_telegram_console.bot.handlers.status.StatusAPI.load_latest_status",
        lambda self: {
            "overall_status": "guarded",
            "generated_at": "2026-04-18T09:00:00+00:00",
            "current_market": {
                "market_id": "678686",
                "market_question": "Will 2026 be the hottest year on record?",
                "comparison_status": "aligned",
                "action_hint": "watch",
            },
            "monitoring": {
                "overall_status": "healthy",
                "worker_count": 2,
                "counts": {"healthy": 2, "warning": 0, "stale": 0, "missing": 0},
                "workers": [{"label": "Market", "status": "healthy"}],
            },
            "probability": {
                "probability_mode": "heuristic_not_calibrated",
                "execution_constraint": "manual_advisory_only",
                "calibration_status": "not_calibrated",
                "confidence_adjusted_edge": 0.03,
            },
            "execution": {
                "status": "blocked",
                "ready_for_live": False,
                "decision": "LIVE_EXECUTION_BLOCKED",
                "blocking_count": 1,
            },
            "operator": {
                "can_bot_trade": False,
                "human_action_required": True,
                "execution_mode": "manual_advisory_only",
            },
            "gate_stack": {
                "data_gate": "pass",
                "resolver_gate": "blocked",
                "probability_gate": "blocked",
                "freshness_gate": "pass",
                "authorization_gate": "blocked",
                "execution_gate": "blocked",
            },
            "block_reasons": ["execution:blocked"],
        },
    )

    update = FakeUpdate()
    asyncio.run(status_handler(update, None))

    assert update.message.parse_mode == "Markdown"
    assert update.message.text is not None
    assert "AARS Unified Status" in update.message.text
    assert "execution:blocked" in update.message.text
    assert "Authorization Gate" in update.message.text
