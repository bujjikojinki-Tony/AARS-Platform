from __future__ import annotations

from types import SimpleNamespace

import weather_telegram_console.app as app_module


class _FakeBuilder:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []

    def token(self, value: str):
        self.calls.append(("token", value))
        return self

    def base_url(self, value: str):
        self.calls.append(("base_url", value))
        return self

    def proxy(self, value: str):
        self.calls.append(("proxy", value))
        return self

    def get_updates_proxy(self, value: str):
        self.calls.append(("get_updates_proxy", value))
        return self

    def build(self):
        self.calls.append(("build", None))
        return _FakeApplication()


class _FakeApplication:
    def __init__(self) -> None:
        self.handlers: list[object] = []
        self.error_handlers: list[object] = []

    def add_handler(self, handler):
        self.handlers.append(handler)

    def add_error_handler(self, handler):
        self.error_handlers.append(handler)


def test_build_app_applies_network_settings(monkeypatch) -> None:
    fake_builder = _FakeBuilder()
    monkeypatch.setattr(
        app_module,
        "Application",
        SimpleNamespace(builder=lambda: fake_builder),
    )
    monkeypatch.setattr(app_module, "get_bot_token", lambda: "token")
    monkeypatch.setattr(app_module, "get_telegram_api_base_url", lambda: "https://example.com/bot")
    monkeypatch.setattr(app_module, "get_telegram_proxy", lambda: "http://proxy.example:8080")
    monkeypatch.setattr(app_module, "get_telegram_get_updates_proxy", lambda: "http://updates.proxy:8080")

    application = app_module.build_app()

    assert application is not None
    assert hasattr(application, "add_handler")
    assert fake_builder.calls == [
        ("token", "token"),
        ("base_url", "https://example.com/bot"),
        ("proxy", "http://proxy.example:8080"),
        ("get_updates_proxy", "http://updates.proxy:8080"),
        ("build", None),
    ]
