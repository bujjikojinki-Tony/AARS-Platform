from __future__ import annotations

from typing import Any, Mapping, Protocol, Sequence, runtime_checkable

from .models import Decision, Evidence, Knowledge, Lesson, Memory, Observation, Outcome

Context = Mapping[str, Any]


@runtime_checkable
class ObservationProvider(Protocol):
    def observe(self, context: Context) -> Sequence[Observation]: ...


@runtime_checkable
class EvidenceProvider(Protocol):
    def produce(self, observation: Observation, context: Context) -> Evidence: ...


@runtime_checkable
class OutcomeValidator(Protocol):
    def validate(
        self, observation: Observation, decision: Decision, context: Context
    ) -> Outcome | None: ...


@runtime_checkable
class MemoryAdapter(Protocol):
    def store_observation(self, observation: Observation, evidence: Evidence) -> None: ...
    def store_outcome(self, outcome: Outcome) -> None: ...
    def store_lesson(self, lesson: Lesson) -> None: ...
    def recall(self, query: Context, limit: int = 10) -> Sequence[Memory]: ...


@runtime_checkable
class KnowledgeAdapter(Protocol):
    def get(self, knowledge_id: str) -> Knowledge | None: ...
    def find(self, query: Context, limit: int = 10) -> Sequence[Knowledge]: ...
    def submit_candidate(self, knowledge: Knowledge) -> None: ...

