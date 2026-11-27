from __future__ import annotations

from importlib.metadata import entry_points

from aars_core.contracts import EvidenceProvider, KnowledgeAdapter, MemoryAdapter, ObservationProvider, OutcomeValidator
from aars_core.plugin import REQUIRED_CAPABILITIES, ResearchPlugin


class PluginValidationError(ValueError):
    pass


class PluginLoader:
    ENTRY_POINT_GROUP = "aars_ros.plugins"

    def __init__(self, core_api_version: str = "1") -> None:
        self.core_api_version = core_api_version
        self._plugins: dict[str, ResearchPlugin] = {}

    def register(self, plugin: ResearchPlugin) -> None:
        self._validate(plugin)
        plugin_id = plugin.manifest.plugin_id
        if plugin_id in self._plugins:
            raise PluginValidationError(f"Plugin already registered: {plugin_id}")
        self._plugins[plugin_id] = plugin

    def discover(self) -> int:
        discovered = 0
        for entry_point in entry_points(group=self.ENTRY_POINT_GROUP):
            self.register(entry_point.load())
            discovered += 1
        return discovered

    def get(self, plugin_id: str) -> ResearchPlugin:
        try:
            return self._plugins[plugin_id]
        except KeyError as exc:
            raise KeyError(f"Plugin not loaded: {plugin_id}") from exc

    def list_plugins(self) -> tuple[ResearchPlugin, ...]:
        return tuple(self._plugins[key] for key in sorted(self._plugins))

    def _validate(self, plugin: ResearchPlugin) -> None:
        manifest = plugin.manifest
        if not manifest.plugin_id or manifest.core_api_version != self.core_api_version:
            raise PluginValidationError("Plugin identity or core API version is invalid")
        if not set(REQUIRED_CAPABILITIES).issubset(manifest.capabilities):
            raise PluginValidationError("Plugin manifest is missing required capabilities")
        checks = (
            (plugin.observation_provider, ObservationProvider),
            (plugin.evidence_provider, EvidenceProvider),
            (plugin.outcome_validator, OutcomeValidator),
            (plugin.memory_adapter, MemoryAdapter),
            (plugin.knowledge_adapter, KnowledgeAdapter),
        )
        if not all(isinstance(component, contract) for component, contract in checks):
            raise PluginValidationError("Plugin does not satisfy the required contracts")

