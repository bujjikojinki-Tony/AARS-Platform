from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable, Mapping

from aars_core.certification import CertificationReport
from aars_core.certification.service import certify_graph
from aars_core.domain import (
    Claim,
    ConformanceError,
    Decision,
    EP01_SPEC_VERSION,
    Evidence,
    Knowledge,
    Lesson,
    Memory,
    ObjectStatus,
    ObjectType,
    Observation,
    Outcome,
    Policy,
    Provenance,
)

from .builders import common_fields, ids, require_objects, require_optional_objects
from .errors import SDKConformanceError


class AARSClient:
    """Stable facade for plugin authors creating AARS reference objects."""

    def __init__(
        self,
        *,
        spec_version: str = EP01_SPEC_VERSION,
        source_id: str = "aars-sdk",
        source_type: str = "sdk",
        source_version: str = "1.0.0",
    ) -> None:
        self.spec_version = spec_version
        self.source_id = source_id
        self.source_type = source_type
        self.source_version = source_version

    def create_observation(
        self,
        *,
        subject: str,
        payload: Mapping[str, Any],
        observed_at: datetime | None = None,
        id: str | None = None,
        created_at: datetime | None = None,
        provenance: Provenance | None = None,
        status: ObjectStatus = ObjectStatus.RECORDED,
        semantic_type: str = "aars.any",
        content_hash: str | None = None,
        source_uri: str | None = None,
    ) -> Observation[Any]:
        common = self._common(
            ObjectType.OBSERVATION, status, id=id, created_at=created_at,
            provenance=provenance, semantic_type=semantic_type,
            content_hash=content_hash, source_uri=source_uri,
        )
        return Observation(
            **common,
            subject=subject,
            observed_at=observed_at or common["created_at"],
            payload=payload,
        )

    def create_evidence(
        self,
        *,
        observations: Iterable[Observation[Any]],
        code: str,
        category: str,
        direction: str,
        weight: float,
        confidence: float,
        value: Any | None = None,
        explanation: str = "",
        id: str | None = None,
        created_at: datetime | None = None,
        provenance: Provenance | None = None,
        status: ObjectStatus = ObjectStatus.ACTIVE,
        semantic_type: str = "aars.any",
        content_hash: str | None = None,
        source_uri: str | None = None,
    ) -> Evidence[Any]:
        observation_values = require_objects("observations", tuple(observations), Observation)
        common = self._common(
            ObjectType.EVIDENCE, status, id=id, created_at=created_at,
            provenance=provenance, semantic_type=semantic_type, content_hash=content_hash,
            source_uri=source_uri, parent_ids=ids(observation_values),
        )
        return Evidence(
            **common, observation_ids=observation_values, code=code, category=category,
            direction=direction, weight=weight, confidence=confidence, value=value,
            explanation=explanation,
        )

    def create_claim(
        self,
        *,
        evidence: Iterable[Evidence[Any]],
        statement: str,
        scope: Mapping[str, Any],
        id: str | None = None,
        created_at: datetime | None = None,
        provenance: Provenance | None = None,
        status: ObjectStatus = ObjectStatus.ACTIVE,
        semantic_type: str = "aars.any",
        content_hash: str | None = None,
        source_uri: str | None = None,
    ) -> Claim[Any]:
        evidence_values = require_objects("evidence", tuple(evidence), Evidence)
        common = self._common(
            ObjectType.CLAIM, status, id=id, created_at=created_at, provenance=provenance,
            semantic_type=semantic_type, content_hash=content_hash, source_uri=source_uri,
            parent_ids=ids(evidence_values),
        )
        return Claim(**common, evidence_ids=evidence_values, statement=statement, scope=scope)

    def create_decision(
        self,
        *,
        claims: Iterable[Claim[Any]],
        level: str,
        posture: str,
        confidence: float,
        rationale: str,
        id: str | None = None,
        created_at: datetime | None = None,
        provenance: Provenance | None = None,
        status: ObjectStatus = ObjectStatus.ACTIVE,
        semantic_type: str = "aars.any",
        content_hash: str | None = None,
        source_uri: str | None = None,
    ) -> Decision[Any]:
        claim_values = require_objects("claims", tuple(claims), Claim)
        common = self._common(
            ObjectType.DECISION, status, id=id, created_at=created_at, provenance=provenance,
            semantic_type=semantic_type, content_hash=content_hash, source_uri=source_uri,
            parent_ids=ids(claim_values),
        )
        return Decision(
            **common, claim_ids=claim_values, level=level, posture=posture,
            confidence=confidence, rationale=rationale,
        )

    def create_outcome(
        self,
        *,
        decisions: Iterable[Decision[Any]] = (),
        claims: Iterable[Claim[Any]] = (),
        measurements: Mapping[str, Any],
        classification: str,
        measured_at: datetime | None = None,
        id: str | None = None,
        created_at: datetime | None = None,
        provenance: Provenance | None = None,
        status: ObjectStatus = ObjectStatus.VALIDATED,
        semantic_type: str = "aars.any",
        content_hash: str | None = None,
        source_uri: str | None = None,
    ) -> Outcome[Any]:
        decision_values = require_optional_objects("decisions", tuple(decisions), Decision)
        claim_values = require_optional_objects("claims", tuple(claims), Claim)
        parent_ids = ids(decision_values) + ids(claim_values)
        common = self._common(
            ObjectType.OUTCOME, status, id=id, created_at=created_at, provenance=provenance,
            semantic_type=semantic_type, content_hash=content_hash, source_uri=source_uri,
            parent_ids=parent_ids,
        )
        return Outcome(
            **common, decision_ids=decision_values, claim_ids=claim_values,
            measured_at=measured_at or common["created_at"], measurements=measurements,
            classification=classification,
        )

    def create_lesson(
        self,
        *,
        outcomes: Iterable[Outcome[Any]],
        alignment: str,
        codes: Iterable[str],
        narrative: str,
        id: str | None = None,
        created_at: datetime | None = None,
        provenance: Provenance | None = None,
        status: ObjectStatus = ObjectStatus.ACTIVE,
        semantic_type: str = "aars.any",
        content_hash: str | None = None,
        source_uri: str | None = None,
    ) -> Lesson[Any]:
        outcome_values = require_objects("outcomes", tuple(outcomes), Outcome)
        common = self._common(
            ObjectType.LESSON, status, id=id, created_at=created_at, provenance=provenance,
            semantic_type=semantic_type, content_hash=content_hash, source_uri=source_uri,
            parent_ids=ids(outcome_values),
        )
        return Lesson(**common, outcome_ids=outcome_values, alignment=alignment, codes=tuple(codes), narrative=narrative)

    def create_memory(
        self,
        *,
        observations: Iterable[Observation[Any]] = (),
        evidence: Iterable[Evidence[Any]] = (),
        claims: Iterable[Claim[Any]] = (),
        decisions: Iterable[Decision[Any]] = (),
        outcomes: Iterable[Outcome[Any]] = (),
        lessons: Iterable[Lesson[Any]] = (),
        id: str | None = None,
        created_at: datetime | None = None,
        provenance: Provenance | None = None,
        status: ObjectStatus = ObjectStatus.ACTIVE,
        semantic_type: str = "aars.any",
        content_hash: str | None = None,
        source_uri: str | None = None,
    ) -> Memory[Any]:
        observation_values = require_optional_objects("observations", tuple(observations), Observation)
        evidence_values = require_optional_objects("evidence", tuple(evidence), Evidence)
        claim_values = require_optional_objects("claims", tuple(claims), Claim)
        decision_values = require_optional_objects("decisions", tuple(decisions), Decision)
        outcome_values = require_optional_objects("outcomes", tuple(outcomes), Outcome)
        lesson_values = require_optional_objects("lessons", tuple(lessons), Lesson)
        parent_ids = (
            ids(observation_values) + ids(evidence_values) + ids(claim_values)
            + ids(decision_values) + ids(outcome_values) + ids(lesson_values)
        )
        common = self._common(
            ObjectType.MEMORY, status, id=id, created_at=created_at, provenance=provenance,
            semantic_type=semantic_type, content_hash=content_hash, source_uri=source_uri,
            parent_ids=parent_ids,
        )
        return Memory(
            **common, observation_ids=observation_values, evidence_ids=evidence_values,
            claim_ids=claim_values, decision_ids=decision_values, outcome_ids=outcome_values,
            lesson_ids=lesson_values,
        )

    def create_knowledge(
        self,
        *,
        lessons: Iterable[Lesson[Any]],
        claim: str,
        scope: Mapping[str, Any],
        id: str | None = None,
        created_at: datetime | None = None,
        provenance: Provenance | None = None,
        status: ObjectStatus = ObjectStatus.ACCEPTED,
        semantic_type: str = "aars.any",
        content_hash: str | None = None,
        source_uri: str | None = None,
    ) -> Knowledge[Any]:
        lesson_values = require_objects("lessons", tuple(lessons), Lesson)
        common = self._common(
            ObjectType.KNOWLEDGE, status, id=id, created_at=created_at, provenance=provenance,
            semantic_type=semantic_type, content_hash=content_hash, source_uri=source_uri,
            parent_ids=ids(lesson_values),
        )
        return Knowledge(**common, lesson_ids=lesson_values, claim=claim, scope=scope)

    def create_policy(
        self,
        *,
        knowledge: Iterable[Knowledge[Any]],
        rule: str,
        authority: str,
        scope: Mapping[str, Any],
        id: str | None = None,
        created_at: datetime | None = None,
        provenance: Provenance | None = None,
        status: ObjectStatus = ObjectStatus.EFFECTIVE,
        semantic_type: str = "aars.any",
        content_hash: str | None = None,
        source_uri: str | None = None,
    ) -> Policy[Any]:
        knowledge_values = require_objects("knowledge", tuple(knowledge), Knowledge)
        common = self._common(
            ObjectType.POLICY, status, id=id, created_at=created_at, provenance=provenance,
            semantic_type=semantic_type, content_hash=content_hash, source_uri=source_uri,
            parent_ids=ids(knowledge_values),
        )
        return Policy(**common, knowledge_ids=knowledge_values, rule=rule, authority=authority, scope=scope)

    def certify(self, objects: Iterable[object]) -> CertificationReport:
        try:
            return certify_graph(objects)  # type: ignore[arg-type]
        except ConformanceError as exc:
            raise SDKConformanceError(str(exc)) from exc

    def _common(
        self,
        object_type: ObjectType,
        status: ObjectStatus,
        **kwargs: Any,
    ) -> dict[str, Any]:
        return common_fields(
            object_type=object_type,
            status=status,
            spec_version=self.spec_version,
            source_id=self.source_id,
            source_type=self.source_type,
            source_version=self.source_version,
            **kwargs,
        )
