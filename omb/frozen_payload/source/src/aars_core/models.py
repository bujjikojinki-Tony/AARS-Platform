from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class Provenance:
    source: str
    source_version: str
    collected_at_utc: str
    content_hash: str


@dataclass(frozen=True)
class Observation:
    observation_id: str
    plugin_id: str
    observed_at_utc: str
    subject: str
    payload: Mapping[str, Any]
    provenance: Provenance


@dataclass(frozen=True)
class EvidenceItem:
    code: str
    direction: str
    weight: float
    confidence: float
    value: Any = None
    explanation: str = ""


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    observation_id: str
    plugin_id: str
    taxonomy_version: str
    items: tuple[EvidenceItem, ...]


@dataclass(frozen=True)
class Decision:
    decision_id: str
    observation_id: str
    evidence_ids: tuple[str, ...]
    level: str
    posture: str
    confidence: float
    rationale: str
    policy_version: str


@dataclass(frozen=True)
class Outcome:
    outcome_id: str
    observation_id: str
    decision_id: str
    validator_version: str
    measured_at_utc: str
    status: str
    values: Mapping[str, Any]


@dataclass(frozen=True)
class Lesson:
    lesson_id: str
    observation_id: str
    outcome_id: str
    rule_version: str
    alignment: str
    codes: tuple[str, ...]
    narrative: str


@dataclass(frozen=True)
class Memory:
    memory_id: str
    plugin_id: str
    pattern_key: str
    observation_ids: tuple[str, ...]
    outcome_ids: tuple[str, ...]
    lesson_ids: tuple[str, ...]
    memory_version: str


@dataclass(frozen=True)
class Knowledge:
    knowledge_id: str
    plugin_id: str
    claim: str
    scope: Mapping[str, Any]
    memory_ids: tuple[str, ...]
    supporting_lesson_ids: tuple[str, ...]
    challenging_lesson_ids: tuple[str, ...]
    status: str
    knowledge_version: str
