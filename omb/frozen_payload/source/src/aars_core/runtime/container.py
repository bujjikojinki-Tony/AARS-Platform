from __future__ import annotations

from typing import Any, Callable


class DependencyContainer:
    """Minimal explicit dependency registry; it contains no domain behavior."""

    def __init__(self) -> None:
        self._providers: dict[str, Callable[[], Any]] = {}

    def register(self, key: str, provider: Callable[[], Any]) -> None:
        if key in self._providers:
            raise ValueError(f"Dependency already registered: {key}")
        self._providers[key] = provider

    def register_instance(self, key: str, value: Any) -> None:
        self.register(key, lambda: value)

    def resolve(self, key: str) -> Any:
        try:
            provider = self._providers[key]
        except KeyError as exc:
            raise KeyError(f"Dependency not registered: {key}") from exc
        return provider()

