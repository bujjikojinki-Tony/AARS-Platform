from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Generic, Mapping, TypeVar, cast

from .common import AARSObject, ObjectType, require_text

T_co = TypeVar("T_co", covariant=True)


@dataclass(frozen=True, kw_only=True)
class TypedReference(Generic[T_co]):
    """Serializable relationship metadata for early semantic validation."""

    id: str
    object_type: ObjectType
    semantic_type: str = "aars.any"

    def __post_init__(self) -> None:
        require_text("id", self.id)
        if not isinstance(self.object_type, ObjectType):
            raise TypeError("object_type must be an ObjectType")
        require_text("semantic_type", self.semantic_type)


ReferenceInput = str | TypedReference[object] | AARSObject


RELATIONSHIP_RULES: Mapping[ObjectType, Mapping[str, ObjectType]] = MappingProxyType({
    ObjectType.EVIDENCE: MappingProxyType({"observation_ids": ObjectType.OBSERVATION}),
    ObjectType.CLAIM: MappingProxyType({"evidence_ids": ObjectType.EVIDENCE}),
    ObjectType.DECISION: MappingProxyType({"claim_ids": ObjectType.CLAIM}),
    ObjectType.OUTCOME: MappingProxyType({
        "decision_ids": ObjectType.DECISION, "claim_ids": ObjectType.CLAIM,
    }),
    ObjectType.LESSON: MappingProxyType({"outcome_ids": ObjectType.OUTCOME}),
    ObjectType.MEMORY: MappingProxyType({
        "observation_ids": ObjectType.OBSERVATION, "evidence_ids": ObjectType.EVIDENCE,
        "claim_ids": ObjectType.CLAIM, "decision_ids": ObjectType.DECISION,
        "outcome_ids": ObjectType.OUTCOME, "lesson_ids": ObjectType.LESSON,
    }),
    ObjectType.KNOWLEDGE: MappingProxyType({"lesson_ids": ObjectType.LESSON}),
    ObjectType.POLICY: MappingProxyType({"knowledge_ids": ObjectType.KNOWLEDGE}),
})


def reference_to(target: T_co) -> TypedReference[T_co]:
    if not isinstance(target, AARSObject):
        raise TypeError("target must be an AARSObject")
    return TypedReference(id=target.id, object_type=target.type, semantic_type=target.semantic_type)


def normalize_references(source: AARSObject, field_name: str, values: tuple[ReferenceInput, ...]) -> tuple[str, ...]:
    if not isinstance(values, tuple):
        raise TypeError(f"{field_name} must be a tuple")
    expected = RELATIONSHIP_RULES.get(source.type, {}).get(field_name)
    if expected is None:
        raise TypeError(f"{source.type.value}.{field_name} is not a declared relationship")
    normalized: list[str] = []
    for value in values:
        if isinstance(value, str):
            normalized.append(value)
            continue
        if isinstance(value, TypedReference):
            target_id, actual, semantic_type = value.id, value.object_type, value.semantic_type
        elif isinstance(value, AARSObject):
            target_id, actual, semantic_type = value.id, value.type, value.semantic_type
        else:
            raise TypeError(f"{field_name} must contain ids, TypedReference values, or AARSObject values")
        if actual is not expected:
            raise TypeError(
                f"{source.type.value}.{field_name} must reference {expected.value}, not {actual.value}"
            )
        if not semantic_types_compatible(source.semantic_type, semantic_type):
            raise TypeError(
                f"{source.type.value}.{field_name} semantic type {semantic_type!r} "
                f"is incompatible with {source.semantic_type!r}"
            )
        normalized.append(target_id)
    return tuple(normalized)


def semantic_types_compatible(source: str, target: str) -> bool:
    return source == "aars.any" or target == "aars.any" or source == target
