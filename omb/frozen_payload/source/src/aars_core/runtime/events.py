from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping


@dataclass(frozen=True)
class Event:
    event_id: str
    topic: str
    source: str
    occurred_at_utc: str
    payload: Mapping[str, Any]


class EventDispatchError(RuntimeError):
    def __init__(self, event: Event, failures: tuple[Exception, ...]) -> None:
        super().__init__(f"{len(failures)} handler(s) failed for topic {event.topic}")
        self.event = event
        self.failures = failures


class EventBus:
    """Synchronous in-process bus with deterministic subscription order."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[tuple[int, Callable[[Event], None]]]] = {}
        self._next_token = 1

    def subscribe(self, topic: str, handler: Callable[[Event], None]) -> int:
        if not topic:
            raise ValueError("topic is required")
        token = self._next_token
        self._next_token += 1
        self._handlers.setdefault(topic, []).append((token, handler))
        return token

    def unsubscribe(self, token: int) -> bool:
        for handlers in self._handlers.values():
            for index, (candidate, _) in enumerate(handlers):
                if candidate == token:
                    handlers.pop(index)
                    return True
        return False

    def publish(self, event: Event) -> int:
        handlers = tuple(self._handlers.get(event.topic, ())) + tuple(self._handlers.get("*", ()))
        failures: list[Exception] = []
        for _, handler in handlers:
            try:
                handler(event)
            except Exception as exc:  # handlers are isolated; failures are reported together
                failures.append(exc)
        if failures:
            raise EventDispatchError(event, tuple(failures))
        return len(handlers)

