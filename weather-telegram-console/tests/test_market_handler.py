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
            "top_parameter_view": {
                "schema_version": "top_parameter_view.v1",
                "market_id": market_id or "mkt_123",
                "market_family": "temperature_daily_max",
                "market_question": "Will NYC hit 95F?",
                "location_name": "New York City",
                "target_date": "2026-07-04",
                "variable_name": "temperature_max",
                "polymarket": {
                    "yes_price": 0.41,
                    "no_price": 0.59,
                    "market_implied_probability": 0.41,
                    "favored_side": "yes",
                    "market_band": "91-95F",
                },
                "weather": {
                    "forecast_value": 93.2,
                    "station_id": "USW00094728",
                    "station_name": "Central Park",
                    "freshness_status": "healthy",
                },
                "source_contract": {
                    "source_match_grade": "exact_station",
                    "freshness_status": "healthy",
                },
                "decision": {
                    "can_execute": "no",
                    "primary_block_reason": "shadow_only",
                },
            },
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
