from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Generic, Mapping, TypeVar

from .common import (
    AARSObject, ObjectStatus, ObjectType, freeze_mapping, require_aware_datetime,
    require_probability, require_refs, require_text,
)
from .semantic_types import TypedReference, normalize_references

T = TypeVar("T")

_COMMON_TERMINAL = frozenset({ObjectStatus.SUPERSEDED, ObjectStatus.RETIRED, ObjectStatus.REJECTED})


@dataclass(frozen=True, kw_only=True)
class Observation(AARSObject, Generic[T]):
    subject: str
    observed_at: datetime
    payload: Mapping[str, Any]

    def __post_init__(self) -> None:
        super().__post_init__()
        self._expect_type(ObjectType.OBSERVATION)
        self._expect_status(frozenset({ObjectStatus.RECORDED, ObjectStatus.FROZEN}) | _COMMON_TERMINAL)
        require_text("subject", self.subject)
        require_aware_datetime("observed_at", self.observed_at)
        if self.observed_at > self.created_at:
            raise ValueError("observed_at cannot be later than created_at")
        freeze_mapping(self, "payload")


@dataclass(frozen=True, kw_only=True)
class Evidence(AARSObject, Generic[T]):
    observation_ids: tuple[str | TypedReference[Observation[T]] | Observation[T], ...]
    code: str
    category: str
    direction: str
    weight: float
    confidence: float
    value: T | None = None
    explanation: str = ""

    def __post_init__(self) -> None:
        super().__post_init__()
        self._expect_type(ObjectType.EVIDENCE)
        self._expect_status(frozenset({ObjectStatus.DRAFT, ObjectStatus.VALIDATED, ObjectStatus.ACTIVE}) | _COMMON_TERMINAL)
        object.__setattr__(self, "observation_ids", normalize_references(self, "observation_ids", self.observation_ids))
        require_refs("observation_ids", self.observation_ids)
        require_text("code", self.code); require_text("category", self.category)
        if self.direction not in {"positive", "negative", "neutral"}:
            raise ValueError("direction must be positive, negative, or neutral")
        require_probability("weight", self.weight); require_probability("confidence", self.confidence)
        object.__setattr__(self, "value", _freeze_arbitrary(self.value))


@dataclass(frozen=True, kw_only=True)
class Claim(AARSObject, Generic[T]):
    evidence_ids: tuple[str | TypedReference[Evidence[T]] | Evidence[T], ...]
    statement: str
    scope: Mapping[str, Any]

    def __post_init__(self) -> None:
        super().__post_init__()
        self._expect_type(ObjectType.CLAIM)
        self._expect_status(frozenset({ObjectStatus.DRAFT, ObjectStatus.VALIDATED, ObjectStatus.ACTIVE}) | _COMMON_TERMINAL)
        object.__setattr__(self, "evidence_ids", normalize_references(self, "evidence_ids", self.evidence_ids))
        require_refs("evidence_ids", self.evidence_ids)
        require_text("statement", self.statement)
        freeze_mapping(self, "scope")


@dataclass(frozen=True, kw_only=True)
class Decision(AARSObject, Generic[T]):
    claim_ids: tuple[str | TypedReference[Claim[T]] | Claim[T], ...]
    level: str
    posture: str
    confidence: float
    rationale: str

    def __post_init__(self) -> None:
        super().__post_init__()
        self._expect_type(ObjectType.DECISION)
        self._expect_status(frozenset({ObjectStatus.DRAFT, ObjectStatus.ACTIVE}) | _COMMON_TERMINAL)
        object.__setattr__(self, "claim_ids", normalize_references(self, "claim_ids", self.claim_ids))
        require_refs("claim_ids", self.claim_ids)
        if self.level not in {"spot", "leverage", "portfolio", "execution"}:
            raise ValueError("level is not a recognized decision level")
        require_text("posture", self.posture); require_text("rationale", self.rationale)
        require_probability("confidence", self.confidence)


@dataclass(frozen=True, kw_only=True)
class Outcome(AARSObject, Generic[T]):
    decision_ids: tuple[str | TypedReference[Decision[T]] | Decision[T], ...]
    claim_ids: tuple[str | TypedReference[Claim[T]] | Claim[T], ...]
    measured_at: datetime
    measurements: Mapping[str, Any]
    classification: str

    def __post_init__(self) -> None:
        super().__post_init__()
        self._expect_type(ObjectType.OUTCOME)
        self._expect_status(frozenset({ObjectStatus.MEASURED, ObjectStatus.VALIDATED}) | _COMMON_TERMINAL)
        object.__setattr__(self, "decision_ids", normalize_references(self, "decision_ids", self.decision_ids))
        object.__setattr__(self, "claim_ids", normalize_references(self, "claim_ids", self.claim_ids))
        require_refs("decision_ids", self.decision_ids, allow_empty=True)
        require_refs("claim_ids", self.claim_ids, allow_empty=True)
        if not self.decision_ids and not self.claim_ids:
            raise ValueError("Outcome must reference at least one Decision or Claim")
        require_aware_datetime("measured_at", self.measured_at)
        if self.measured_at > self.created_at:
            raise ValueError("measured_at cannot be later than created_at")
        require_text("classification", self.classification)
        freeze_mapping(self, "measurements")


@dataclass(frozen=True, kw_only=True)
class Lesson(AARSObject, Generic[T]):
    outcome_ids: tuple[str | TypedReference[Outcome[T]] | Outcome[T], ...]
    alignment: str
    codes: tuple[str, ...]
    narrative: str

    def __post_init__(self) -> None:
        super().__post_init__()
        self._expect_type(ObjectType.LESSON)
        self._expect_status(frozenset({ObjectStatus.DRAFT, ObjectStatus.VALIDATED, ObjectStatus.ACTIVE}) | _COMMON_TERMINAL)
        object.__setattr__(self, "outcome_ids", normalize_references(self, "outcome_ids", self.outcome_ids))
        require_refs("outcome_ids", self.outcome_ids)
        if len(self.outcome_ids) != 1:
            raise ValueError("Lesson must reference exactly one Outcome")
        if self.alignment not in {"supported", "challenged", "inconclusive"}:
            raise ValueError("alignment must be supported, challenged, or inconclusive")
        require_refs("codes", self.codes)
        require_text("narrative", self.narrative)


@dataclass(frozen=True, kw_only=True)
class Memory(AARSObject, Generic[T]):
    observation_ids: tuple[str | TypedReference[Observation[T]] | Observation[T], ...] = ()
    evidence_ids: tuple[str | TypedReference[Evidence[T]] | Evidence[T], ...] = ()
    claim_ids: tuple[str | TypedReference[Claim[T]] | Claim[T], ...] = ()
    decision_ids: tuple[str | TypedReference[Decision[T]] | Decision[T], ...] = ()
    outcome_ids: tuple[str | TypedReference[Outcome[T]] | Outcome[T], ...] = ()
    lesson_ids: tuple[str | TypedReference[Lesson[T]] | Lesson[T], ...] = ()

    def __post_init__(self) -> None:
        super().__post_init__()
        self._expect_type(ObjectType.MEMORY)
        self._expect_status(frozenset({ObjectStatus.DRAFT, ObjectStatus.ACTIVE, ObjectStatus.FROZEN}) | _COMMON_TERMINAL)
        for field_name in ("observation_ids", "evidence_ids", "claim_ids", "decision_ids", "outcome_ids", "lesson_ids"):
            object.__setattr__(self, field_name, normalize_references(self, field_name, getattr(self, field_name)))
            require_refs(field_name, getattr(self, field_name), allow_empty=True)
        if not any((self.observation_ids, self.evidence_ids, self.claim_ids, self.decision_ids, self.outcome_ids, self.lesson_ids)):
            raise ValueError("Memory must retain at least one domain object")


@dataclass(frozen=True, kw_only=True)
class Knowledge(AARSObject, Generic[T]):
    lesson_ids: tuple[str | TypedReference[Lesson[T]] | Lesson[T], ...]
    claim: str
    scope: Mapping[str, Any]

    def __post_init__(self) -> None:
        super().__post_init__()
        self._expect_type(ObjectType.KNOWLEDGE)
        self._expect_status(frozenset({ObjectStatus.DRAFT, ObjectStatus.CANDIDATE, ObjectStatus.ACCEPTED}) | _COMMON_TERMINAL)
        object.__setattr__(self, "lesson_ids", normalize_references(self, "lesson_ids", self.lesson_ids))
        require_refs("lesson_ids", self.lesson_ids)
        require_text("claim", self.claim)
        freeze_mapping(self, "scope")


@dataclass(frozen=True, kw_only=True)
class Policy(AARSObject, Generic[T]):
    knowledge_ids: tuple[str | TypedReference[Knowledge[T]] | Knowledge[T], ...]
    rule: str
    authority: str
    scope: Mapping[str, Any]

    def __post_init__(self) -> None:
        super().__post_init__()
        self._expect_type(ObjectType.POLICY)
        self._expect_status(frozenset({ObjectStatus.DRAFT, ObjectStatus.CANDIDATE, ObjectStatus.ACCEPTED, ObjectStatus.EFFECTIVE}) | _COMMON_TERMINAL)
        object.__setattr__(self, "knowledge_ids", normalize_references(self, "knowledge_ids", self.knowledge_ids))
        require_refs("knowledge_ids", self.knowledge_ids)
        require_text("rule", self.rule); require_text("authority", self.authority)
        freeze_mapping(self, "scope")


def _freeze_arbitrary(value: Any) -> Any:
    from .common import freeze_value
    return freeze_value(value)
