from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, TypeVar, overload

from aars_core.certification.models import (
    ConformanceReport,
    SpecificationViolation,
    ViolationCategory,
    ViolationSeverity,
)
from aars_core.certification.reporting import build_conformance_report

from .common import AARSObject, EP01_SPEC_VERSION, ObjectStatus, ObjectType
from .objects import Claim, Decision, Evidence, Knowledge, Lesson, Memory, Observation, Outcome, Policy
from .semantic_types import semantic_types_compatible


@dataclass(frozen=True)
class ConformanceViolation:
    code: str
    object_id: str
    message: str
    related_id: str | None = None
    severity: ViolationSeverity = ViolationSeverity.ERROR


class ConformanceError(ValueError):
    def __init__(self, violations: tuple[ConformanceViolation, ...], report: ConformanceReport | None = None) -> None:
        super().__init__(f"EP-01 conformance failed with {len(violations)} violation(s)")
        self.violations = violations
        self.report = report


T = TypeVar("T", bound=AARSObject)


@overload
def validate_graph(objects: Iterable[AARSObject], *, raise_on_error: bool = True, return_report: bool = False) -> tuple[ConformanceViolation, ...]: ...


@overload
def validate_graph(objects: Iterable[AARSObject], *, raise_on_error: bool = True, return_report: bool = True) -> ConformanceReport: ...


def validate_graph(
    objects: Iterable[AARSObject], *, raise_on_error: bool = True, return_report: bool = False,
) -> tuple[ConformanceViolation, ...] | ConformanceReport:
    values = tuple(objects)
    violations: list[ConformanceViolation] = []
    index: dict[str, AARSObject] = {}
    for value in values:
        if value.id in index:
            violations.append(ConformanceViolation("EP01-ID-DUPLICATE", value.id, "Object id must be unique"))
        else:
            index[value.id] = value
        if value.spec_version != EP01_SPEC_VERSION:
            violations.append(ConformanceViolation(
                "EP01-SPEC-VERSION", value.id,
                f"Reference implementation requires spec_version {EP01_SPEC_VERSION}",
            ))

    for value in values:
        if isinstance(value, Evidence):
            _check_refs(value, value.observation_ids, Observation, index, violations, "observation_ids")
        elif isinstance(value, Claim):
            _check_refs(value, value.evidence_ids, Evidence, index, violations, "evidence_ids")
        elif isinstance(value, Decision):
            _check_refs(value, value.claim_ids, Claim, index, violations, "claim_ids")
        elif isinstance(value, Outcome):
            _check_refs(value, value.decision_ids, Decision, index, violations, "decision_ids")
            _check_refs(value, value.claim_ids, Claim, index, violations, "claim_ids")
        elif isinstance(value, Lesson):
            _check_refs(value, value.outcome_ids, Outcome, index, violations, "outcome_ids")
        elif isinstance(value, Memory):
            _check_refs(value, value.observation_ids, Observation, index, violations, "observation_ids")
            _check_refs(value, value.evidence_ids, Evidence, index, violations, "evidence_ids")
            _check_refs(value, value.claim_ids, Claim, index, violations, "claim_ids")
            _check_refs(value, value.decision_ids, Decision, index, violations, "decision_ids")
            _check_refs(value, value.outcome_ids, Outcome, index, violations, "outcome_ids")
            _check_refs(value, value.lesson_ids, Lesson, index, violations, "lesson_ids")
        elif isinstance(value, Knowledge):
            lessons = _check_refs(value, value.lesson_ids, Lesson, index, violations, "lesson_ids")
            if value.status == ObjectStatus.ACCEPTED:
                for lesson in lessons:
                    if lesson.status not in {ObjectStatus.VALIDATED, ObjectStatus.ACTIVE}:
                        violations.append(ConformanceViolation(
                            "EP01-KNOWLEDGE-PROMOTION", value.id,
                            "Accepted Knowledge requires validated or active Lessons", lesson.id,
                        ))
        elif isinstance(value, Policy):
            knowledge = _check_refs(value, value.knowledge_ids, Knowledge, index, violations, "knowledge_ids")
            if value.status in {ObjectStatus.ACCEPTED, ObjectStatus.EFFECTIVE}:
                for item in knowledge:
                    if item.status != ObjectStatus.ACCEPTED:
                        violations.append(ConformanceViolation(
                            "EP01-POLICY-PROMOTION", value.id,
                            "Accepted or effective Policy requires accepted Knowledge", item.id,
                        ))

    ordered = tuple(sorted(violations, key=lambda item: (item.object_id, item.code, item.related_id or "")))
    structured = tuple(_structure_violation(item, index) for item in ordered)
    report = build_conformance_report(
        spec_version=EP01_SPEC_VERSION,
        object_count=len(values),
        relationship_count=sum(_relationship_count(value) for value in values),
        violations=structured,
    )
    if return_report:
        return report
    if report.summary["error_count"] and raise_on_error:
        raise ConformanceError(ordered, report)
    return ordered


def _check_refs(
    source: AARSObject,
    refs: tuple[str, ...],
    expected: type[T],
    index: dict[str, AARSObject],
    violations: list[ConformanceViolation],
    field_name: str,
) -> tuple[T, ...]:
    resolved: list[T] = []
    for ref in refs:
        target = index.get(ref)
        if target is None:
            violations.append(ConformanceViolation(
                "EP01-REF-MISSING", source.id,
                f"{field_name} references a missing {expected.__name__}", ref,
            ))
            continue
        if not isinstance(target, expected):
            violations.append(ConformanceViolation(
                "EP01-REF-TYPE", source.id,
                f"{field_name} must reference {expected.__name__}, not {target.__class__.__name__}", ref,
            ))
            continue
        resolved.append(target)
        if not semantic_types_compatible(source.semantic_type, target.semantic_type):
            violations.append(ConformanceViolation(
                "EP05-REF-SEMANTIC", source.id,
                f"{field_name} semantic type {target.semantic_type!r} is incompatible with {source.semantic_type!r}", ref,
            ))
        if target.created_at > source.created_at:
            violations.append(ConformanceViolation(
                "EP01-REF-TIME", source.id,
                "Derived object cannot predate a referenced source object", ref,
            ))
        if target.status == ObjectStatus.REJECTED:
            violations.append(ConformanceViolation(
                "EP01-REF-REJECTED", source.id,
                "Active lineage cannot derive from a rejected object", ref,
            ))
        elif target.status == ObjectStatus.SUPERSEDED:
            violations.append(ConformanceViolation(
                "EP01-REF-SUPERSEDED", source.id,
                "Lineage references a superseded object", ref, ViolationSeverity.WARNING,
            ))
    return tuple(resolved)


def _structure_violation(
    violation: ConformanceViolation, index: dict[str, AARSObject],
) -> SpecificationViolation:
    source = index.get(violation.object_id)
    target = index.get(violation.related_id or "")
    rule_id = _rule_id(source)
    category = ViolationCategory.RELATIONSHIP
    expected: object = "conforming relationship"
    actual: object = violation.code

    if violation.code in {"EP01-ID-DUPLICATE", "EP01-SPEC-VERSION"}:
        category = ViolationCategory.METADATA
        rule_id = "SPEC-0100"
    elif violation.code == "EP01-REF-TIME":
        category = ViolationCategory.TRACEABILITY
        expected, actual = "referenced.created_at <= source.created_at", "referenced object is newer"
    elif violation.code in {"EP01-REF-REJECTED", "EP01-REF-SUPERSEDED"}:
        category = ViolationCategory.LIFECYCLE
        expected = "eligible lifecycle status"
        actual = target.status.value if target else "missing"
    elif violation.code == "EP01-REF-MISSING":
        expected, actual = "existing referenced object", "missing"
    elif violation.code == "EP01-REF-TYPE":
        expected = _expected_reference_type(source, violation.related_id)
        actual = target.__class__.__name__ if target else "missing"
    elif violation.code == "EP05-REF-SEMANTIC":
        category = ViolationCategory.ONTOLOGY
        expected = source.semantic_type if source else "compatible semantic type"
        actual = target.semantic_type if target else "missing"
    elif violation.code in {"EP01-KNOWLEDGE-PROMOTION", "EP01-POLICY-PROMOTION"}:
        category = ViolationCategory.LIFECYCLE
        expected = "eligible promotion source"
        actual = target.status.value if target else "missing"

    return SpecificationViolation(
        rule_id=rule_id,
        code=violation.code,
        severity=violation.severity,
        category=category,
        object_id=violation.object_id,
        object_type=source.type.value if source else "unknown",
        expected=expected,
        actual=actual,
        message=violation.message,
        trace_path=tuple(item for item in (violation.object_id, violation.related_id) if item),
    )


def _rule_id(source: AARSObject | None) -> str:
    sections = {
        ObjectType.OBSERVATION: "SPEC-0210", ObjectType.EVIDENCE: "SPEC-0220",
        ObjectType.CLAIM: "SPEC-0230", ObjectType.DECISION: "SPEC-0240",
        ObjectType.OUTCOME: "SPEC-0250", ObjectType.LESSON: "SPEC-0260",
        ObjectType.MEMORY: "SPEC-0270", ObjectType.KNOWLEDGE: "SPEC-0280",
        ObjectType.POLICY: "SPEC-0290",
    }
    return sections.get(source.type, "SPEC-0100") if source else "SPEC-0100"


def _expected_reference_type(source: AARSObject | None, related_id: str | None) -> str:
    del related_id
    expected = {
        Evidence: "Observation", Claim: "Evidence", Decision: "Claim",
        Lesson: "Outcome", Knowledge: "Lesson", Policy: "Knowledge",
    }
    return expected.get(type(source), "declared relationship type")


def _relationship_count(value: AARSObject) -> int:
    fields = (
        "observation_ids", "evidence_ids", "claim_ids", "decision_ids",
        "outcome_ids", "lesson_ids", "knowledge_ids",
    )
    return sum(len(getattr(value, field, ())) for field in fields)


EXPECTED_TYPES = {
    Observation: ObjectType.OBSERVATION,
    Evidence: ObjectType.EVIDENCE,
    Claim: ObjectType.CLAIM,
    Decision: ObjectType.DECISION,
    Outcome: ObjectType.OUTCOME,
    Lesson: ObjectType.LESSON,
    Memory: ObjectType.MEMORY,
    Knowledge: ObjectType.KNOWLEDGE,
    Policy: ObjectType.POLICY,
}
