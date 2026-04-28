from types import SimpleNamespace

from weather_telegram_console.bot.handlers import text_commands


def test_text_command_router_routes_plain_text_market(monkeypatch) -> None:
    called: list[str] = []

    async def fake_market_handler(update, context):
        called.append("market")

    monkeypatch.setattr(text_commands, "market_handler", fake_market_handler)

    update = SimpleNamespace(message=SimpleNamespace(text="market"))
    context = SimpleNamespace()

    import asyncio

    asyncio.run(text_commands.text_command_router(update, context))

    assert called == ["market"]


def test_text_command_router_routes_plain_text_signal(monkeypatch) -> None:
    called: list[str] = []

    async def fake_signals_handler(update, context):
        called.append("signals")

    monkeypatch.setattr(text_commands, "signals_handler", fake_signals_handler)

    update = SimpleNamespace(message=SimpleNamespace(text="signal"))
    context = SimpleNamespace()

    import asyncio

    asyncio.run(text_commands.text_command_router(update, context))

    assert called == ["signals"]


def test_text_command_router_routes_plain_text_monitoring(monkeypatch) -> None:
    called: list[str] = []

    async def fake_monitoring_handler(update, context):
        called.append("monitoring")

    monkeypatch.setattr(text_commands, "monitoring_handler", fake_monitoring_handler)

    update = SimpleNamespace(message=SimpleNamespace(text="monitoring"))
    context = SimpleNamespace()

    import asyncio

    asyncio.run(text_commands.text_command_router(update, context))

    assert called == ["monitoring"]


def test_text_command_router_routes_plain_text_operations_monitor(monkeypatch) -> None:
    called: list[str] = []

    async def fake_operations_monitor_handler(update, context):
        called.append("operations_monitor")

    monkeypatch.setattr(text_commands, "operations_monitor_handler", fake_operations_monitor_handler)

    update = SimpleNamespace(message=SimpleNamespace(text="/monitor"))
    context = SimpleNamespace()

    import asyncio

    asyncio.run(text_commands.text_command_router(update, context))

    assert called == ["operations_monitor"]
