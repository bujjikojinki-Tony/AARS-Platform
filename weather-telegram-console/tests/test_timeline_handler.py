import asyncio

from weather_telegram_console.bot.handlers.timeline import timeline_handler


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


class FakeContext:
    def __init__(self, args: list[str] | None = None) -> None:
        self.args = args or []


def test_timeline_handler(monkeypatch) -> None:
    monkeypatch.setattr(
        "weather_telegram_console.bot.handlers.timeline.MarketAPI.load_market_timeline",
        lambda self, market_id=None: [
            {
                "market_id": market_id or "mkt_123",
                "timestamp": "2026-04-18T09:00:00+00:00",
                "comparison_status": "aligned",
                "action_hint": "watch",
                "market_band": "91-95F",
                "model_band": "91-95F",
                "model_value": 93.1,
                "confidence_adjusted_gap": 0.03,
                "confidence_score": 0.81,
            }
        ],
    )

    update = FakeUpdate()
    context = FakeContext(["mkt_123"])
    asyncio.run(timeline_handler(update, context))

    assert update.message.parse_mode == "Markdown"
    assert update.message.text is not None
    assert "AARS Market Timeline" in update.message.text
    assert "2026-04-18T09:00:00+00:00" in update.message.text


def test_timeline_handler_not_found(monkeypatch) -> None:
    def _raise(self, market_id=None):
        raise FileNotFoundError("No comparison history is available for the selected market.")

    monkeypatch.setattr(
        "weather_telegram_console.bot.handlers.timeline.MarketAPI.load_market_timeline",
        _raise,
    )

    update = FakeUpdate()
    context = FakeContext(["missing"])
    asyncio.run(timeline_handler(update, context))

    assert update.message.text == "No comparison history is available for the selected market."
