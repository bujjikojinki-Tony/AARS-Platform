from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .contracts import EvidenceProvider, KnowledgeAdapter, MemoryAdapter, ObservationProvider, OutcomeValidator


@dataclass(frozen=True)
class PluginManifest:
    plugin_id: str
    name: str
    version: str
    domain: str
    core_api_version: str
    capabilities: tuple[str, ...]


class ResearchPlugin(Protocol):
    manifest: PluginManifest
    observation_provider: ObservationProvider
    evidence_provider: EvidenceProvider
    outcome_validator: OutcomeValidator
    memory_adapter: MemoryAdapter
    knowledge_adapter: KnowledgeAdapter


REQUIRED_CAPABILITIES = (
    "observations", "evidence", "outcome_validation", "memory", "knowledge"
)

