from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence

from aars_core.models import Decision, Evidence, Lesson, Observation, Outcome

from aars_core.plugin import ResearchPlugin


class PluginResolver(Protocol):
    def get(self, plugin_id: str) -> ResearchPlugin: ...


@dataclass(frozen=True)
class LifecycleCase:
    plugin_id: str
    observation: Observation
    evidence: Evidence


class LifecycleManager:
    """Coordinates contract transitions without supplying domain decisions."""

    def __init__(self, plugins: PluginResolver) -> None:
        self.plugins = plugins

    def observe(self, plugin_id: str, context: Mapping[str, Any]) -> Sequence[LifecycleCase]:
        plugin = self.plugins.get(plugin_id)
        cases: list[LifecycleCase] = []
        for observation in plugin.observation_provider.observe(context):
            if observation.plugin_id != plugin_id:
                raise ValueError("Observation plugin_id does not match the loaded plugin")
            evidence = plugin.evidence_provider.produce(observation, context)
            if evidence.observation_id != observation.observation_id or evidence.plugin_id != plugin_id:
                raise ValueError("Evidence provenance does not match its observation")
            plugin.memory_adapter.store_observation(observation, evidence)
            cases.append(LifecycleCase(plugin_id, observation, evidence))
        return tuple(cases)

    def validate_outcome(
        self,
        case: LifecycleCase,
        decision: Decision,
        context: Mapping[str, Any],
    ) -> Outcome | None:
        if decision.observation_id != case.observation.observation_id:
            raise ValueError("Decision does not belong to the lifecycle observation")
        outcome = self.plugins.get(case.plugin_id).outcome_validator.validate(
            case.observation, decision, context
        )
        if outcome is not None:
            if outcome.observation_id != case.observation.observation_id:
                raise ValueError("Outcome does not belong to the lifecycle observation")
            self.plugins.get(case.plugin_id).memory_adapter.store_outcome(outcome)
        return outcome

    def store_lesson(self, plugin_id: str, lesson: Lesson) -> None:
        self.plugins.get(plugin_id).memory_adapter.store_lesson(lesson)

    def recall(self, plugin_id: str, query: Mapping[str, Any], limit: int = 10):
        return self.plugins.get(plugin_id).memory_adapter.recall(query, limit)

    def find_knowledge(self, plugin_id: str, query: Mapping[str, Any], limit: int = 10):
        return self.plugins.get(plugin_id).knowledge_adapter.find(query, limit)
