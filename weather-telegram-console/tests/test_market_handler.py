import asyncio

from weather_telegram_console.bot.handlers.market import market_handler


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


def test_market_handler(monkeypatch) -> None:
    monkeypatch.setattr(
        "weather_telegram_console.bot.handlers.market.MarketAPI.load_market_summary",
        lambda self, market_id=None: {
            "market_id": market_id or "mkt_123",
            "market_question": "Will NYC hit 95F?",
            "comparison_status": "aligned",
        },
    )

    update = FakeUpdate()
    context = FakeContext(["mkt_123"])
    asyncio.run(market_handler(update, context))

    assert update.message.parse_mode == "Markdown"
    assert update.message.text is not None
    assert "AARS Market Snapshot" in update.message.text
    assert "mkt_123" in update.message.text


def test_market_handler_not_found(monkeypatch) -> None:
    def _raise(self, market_id=None):
        raise FileNotFoundError("Selected market is not available in the latest market summary.")

    monkeypatch.setattr(
        "weather_telegram_console.bot.handlers.market.MarketAPI.load_market_summary",
        _raise,
    )

    update = FakeUpdate()
    context = FakeContext(["missing"])
    asyncio.run(market_handler(update, context))

    assert update.message.text == "Selected market is not available in the latest market summary."
