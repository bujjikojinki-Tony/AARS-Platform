from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

EP01_SPEC_VERSION = "1.0.0"
_SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


class ObjectType(str, Enum):
    OBSERVATION = "observation"
    EVIDENCE = "evidence"
    CLAIM = "claim"
    DECISION = "decision"
    OUTCOME = "outcome"
    LESSON = "lesson"
    MEMORY = "memory"
    KNOWLEDGE = "knowledge"
    POLICY = "policy"


class ObjectStatus(str, Enum):
    DRAFT = "draft"
    RECORDED = "recorded"
    ACTIVE = "active"
    MEASURED = "measured"
    VALIDATED = "validated"
    CANDIDATE = "candidate"
    ACCEPTED = "accepted"
    EFFECTIVE = "effective"
    FROZEN = "frozen"
    SUPERSEDED = "superseded"
    RETIRED = "retired"
    REJECTED = "rejected"


@dataclass(frozen=True, kw_only=True)
class Provenance:
    source_id: str
    source_type: str
    source_version: str
    collected_at: datetime
    content_hash: str
    source_uri: str | None = None
    parent_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in ("source_id", "source_type", "source_version", "content_hash"):
            _require_text(name, getattr(self, name))
        _require_aware_datetime("collected_at", self.collected_at)
        _require_unique_refs("parent_ids", self.parent_ids, allow_empty=True)


@dataclass(frozen=True, kw_only=True)
class AARSObject:
    id: str
    type: ObjectType
    created_at: datetime
    spec_version: str
    provenance: Provenance
    status: ObjectStatus
    semantic_type: str = "aars.any"

    def __post_init__(self) -> None:
        _require_text("id", self.id)
        _require_aware_datetime("created_at", self.created_at)
        if not isinstance(self.provenance, Provenance):
            raise TypeError("provenance must be a Provenance value")
        _require_text("semantic_type", self.semantic_type)
        if not _SEMVER.fullmatch(self.spec_version):
            raise ValueError("spec_version must be semantic version text")
        if self.created_at < self.provenance.collected_at:
            raise ValueError("created_at cannot precede provenance collection time")

    def _expect_type(self, expected: ObjectType) -> None:
        if self.type != expected:
            raise ValueError(f"{self.__class__.__name__}.type must be {expected.value}")

    def _expect_status(self, allowed: frozenset[ObjectStatus]) -> None:
        if self.status not in allowed:
            names = ", ".join(sorted(status.value for status in allowed))
            raise ValueError(f"{self.__class__.__name__}.status must be one of: {names}")


def freeze_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): freeze_value(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(freeze_value(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(freeze_value(item) for item in value)
    return value


def freeze_mapping(owner: object, field_name: str) -> None:
    value = getattr(owner, field_name)
    if not isinstance(value, Mapping):
        raise TypeError(f"{field_name} must be a mapping")
    object.__setattr__(owner, field_name, freeze_value(value))


def require_refs(field_name: str, refs: tuple[str, ...], allow_empty: bool = False) -> None:
    _require_unique_refs(field_name, refs, allow_empty)


def require_probability(field_name: str, value: float) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= value <= 1:
        raise ValueError(f"{field_name} must be within [0, 1]")


def require_text(field_name: str, value: str) -> None:
    _require_text(field_name, value)


def require_aware_datetime(field_name: str, value: datetime) -> None:
    _require_aware_datetime(field_name, value)


def _require_text(field_name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be non-empty text")


def _require_aware_datetime(field_name: str, value: datetime) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be a timezone-aware datetime")


def _require_unique_refs(field_name: str, refs: tuple[str, ...], allow_empty: bool) -> None:
    if not isinstance(refs, tuple):
        raise TypeError(f"{field_name} must be a tuple")
    if not allow_empty and not refs:
        raise ValueError(f"{field_name} must contain at least one reference")
    if any(not isinstance(ref, str) or not ref.strip() for ref in refs):
        raise ValueError(f"{field_name} contains an invalid reference")
    if len(set(refs)) != len(refs):
        raise ValueError(f"{field_name} must not contain duplicate references")
