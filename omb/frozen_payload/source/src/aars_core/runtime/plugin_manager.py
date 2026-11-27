from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from aars_core.plugin import ResearchPlugin

from .events import Event, EventBus
from .loader import PluginLoader


@dataclass(frozen=True)
class PluginStatus:
    plugin_id: str
    version: str
    domain: str
    state: str


class PluginManager:
    """Owns registration and enablement; plugin code remains external."""

    def __init__(
        self,
        loader: PluginLoader,
        events: EventBus | None = None,
        clock: Callable[[], str] | None = None,
    ) -> None:
        self.loader = loader
        self.events = events
        self.clock = clock or (lambda: datetime.now(timezone.utc).isoformat())
        self._states: dict[str, str] = {}
        self._event_sequence = 0

    def register(self, plugin: ResearchPlugin, enabled: bool = True) -> None:
        self.loader.register(plugin)
        plugin_id = plugin.manifest.plugin_id
        self._states[plugin_id] = "ENABLED" if enabled else "DISABLED"
        self._publish("runtime.plugin.registered", plugin_id, self._states[plugin_id])

    def discover(self, enabled: bool = True) -> int:
        before = {plugin.manifest.plugin_id for plugin in self.loader.list_plugins()}
        count = self.loader.discover()
        for plugin in self.loader.list_plugins():
            if plugin.manifest.plugin_id not in before:
                self._states[plugin.manifest.plugin_id] = "ENABLED" if enabled else "DISABLED"
        return count

    def enable(self, plugin_id: str) -> None:
        self.loader.get(plugin_id)
        self._states[plugin_id] = "ENABLED"
        self._publish("runtime.plugin.enabled", plugin_id, "ENABLED")

    def disable(self, plugin_id: str) -> None:
        self.loader.get(plugin_id)
        self._states[plugin_id] = "DISABLED"
        self._publish("runtime.plugin.disabled", plugin_id, "DISABLED")

    def get(self, plugin_id: str) -> ResearchPlugin:
        plugin = self.loader.get(plugin_id)
        if self._states.get(plugin_id) != "ENABLED":
            raise RuntimeError(f"Plugin is not enabled: {plugin_id}")
        return plugin

    def list_status(self) -> tuple[PluginStatus, ...]:
        return tuple(
            PluginStatus(
                plugin.manifest.plugin_id, plugin.manifest.version,
                plugin.manifest.domain, self._states.get(plugin.manifest.plugin_id, "UNMANAGED"),
            )
            for plugin in self.loader.list_plugins()
        )

    def _publish(self, topic: str, plugin_id: str, state: str) -> None:
        if self.events:
            self._event_sequence += 1
            self.events.publish(Event(
                event_id=f"plugin-manager:{self._event_sequence}", topic=topic,
                source="runtime.plugin_manager", occurred_at_utc=self.clock(),
                payload={"plugin_id": plugin_id, "state": state},
            ))
