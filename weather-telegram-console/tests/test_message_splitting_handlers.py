from __future__ import annotations

import asyncio
from types import SimpleNamespace

from weather_telegram_console.bot.handlers.market import market_handler
from weather_telegram_console.bot.handlers.monitoring import monitoring_handler
from weather_telegram_console.bot.handlers.opportunities import opportunities_handler
from weather_telegram_console.bot.handlers.signals import signals_handler


class FakeMessage:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def reply_text(self, text: str, parse_mode: str | None = None, reply_markup=None) -> None:
        self.calls.append(
            {
                "text": text,
                "parse_mode": parse_mode,
                "reply_markup": reply_markup,
            }
        )


class FakeUpdate:
    def __init__(self) -> None:
        self.message = FakeMessage()


class FakeContext:
    def __init__(self, args: list[str] | None = None) -> None:
        self.args = args or []


def test_monitoring_handler_splits_long_message(monkeypatch) -> None:
    monkeypatch.setattr(
        "weather_telegram_console.bot.handlers.monitoring.MonitoringAPI.load_latest_monitoring_signals",
        lambda self: {"overall_status": "healthy"},
    )
    monkeypatch.setattr(
        "weather_telegram_console.bot.handlers.monitoring.format_monitoring_card",
        lambda payload: "\n\n".join(f"Section {idx}\n{'m' * 1800}" for idx in range(1, 4)),
    )

    update = FakeUpdate()
    asyncio.run(monitoring_handler(update, None))

    assert len(update.message.calls) >= 2
    assert all(len(call["text"]) <= 3500 for call in update.message.calls)


def test_market_handler_splits_long_message(monkeypatch) -> None:
    monkeypatch.setattr(
        "weather_telegram_console.bot.handlers.market.MarketAPI.load_market_summary",
        lambda self, market_id=None: {"market_id": market_id or "mkt_123"},
    )
    monkeypatch.setattr(
        "weather_telegram_console.bot.handlers.market.format_market_card",
        lambda payload: "\n\n".join(f"Section {idx}\n{'x' * 1800}" for idx in range(1, 4)),
    )

    update = FakeUpdate()
    asyncio.run(market_handler(update, FakeContext(["mkt_123"])))

    assert len(update.message.calls) >= 2
    assert all(len(call["text"]) <= 3500 for call in update.message.calls)


def test_opportunities_handler_splits_long_message(monkeypatch) -> None:
    monkeypatch.setattr(
        "weather_telegram_console.bot.handlers.opportunities.OpportunityAPI.load_opportunity_board",
        lambda self, city=None: {"schema_version": "opportunity_board_view.v1", "rows": []},
    )
    monkeypatch.setattr(
        "weather_telegram_console.bot.handlers.opportunities.format_opportunity_board_card",
        lambda payload: "\n\n".join(f"Section {idx}\n{'o' * 1800}" for idx in range(1, 4)),
    )

    update = FakeUpdate()
    asyncio.run(opportunities_handler(update, FakeContext(["Shanghai"])))

    assert len(update.message.calls) >= 2
    assert all(len(call["text"]) <= 3500 for call in update.message.calls)


def test_signals_handler_splits_long_message_and_keeps_keyboard_on_first_chunk(monkeypatch) -> None:
    monkeypatch.setattr(
        "weather_telegram_console.bot.handlers.signals.SignalAPI.load_latest_signal",
        lambda self: {"signal_id": "sig_1"},
    )
    monkeypatch.setattr(
        "weather_telegram_console.bot.handlers.signals.StatusAPI.load_latest_status",
        lambda self: {},
    )
    monkeypatch.setattr(
        "weather_telegram_console.bot.handlers.signals.ApprovalRepository",
        lambda store: SimpleNamespace(get_signal_approval_status=lambda signal_id: {"status": "未审批", "expires_at": None}),
    )
    monkeypatch.setattr(
        "weather_telegram_console.bot.handlers.signals.format_signal_card",
        lambda payload, approval_status=None, approval_expires_at=None, top_parameter_view=None: "\n\n".join(
            f"Section {idx}\n{'s' * 1800}" for idx in range(1, 4)
        ),
    )
    monkeypatch.setattr(
        "weather_telegram_console.bot.handlers.signals.build_signal_actions_keyboard",
        lambda signal_id: {"keyboard_for": signal_id},
    )

    update = FakeUpdate()
    asyncio.run(signals_handler(update, None))

    assert len(update.message.calls) >= 2
    assert all(len(call["text"]) <= 3500 for call in update.message.calls)
    assert update.message.calls[0]["reply_markup"] == {"keyboard_for": "sig_1"}
    assert all(call["reply_markup"] is None for call in update.message.calls[1:])
