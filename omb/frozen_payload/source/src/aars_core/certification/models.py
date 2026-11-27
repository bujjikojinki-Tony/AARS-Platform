from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class ViolationSeverity(str, Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


class ViolationCategory(str, Enum):
    ONTOLOGY = "Ontology"
    RELATIONSHIP = "Relationship"
    LIFECYCLE = "Lifecycle"
    METADATA = "Metadata"
    TRACEABILITY = "Traceability"


class CertificationLevel(str, Enum):
    CERTIFIED = "CERTIFIED"
    COMPATIBLE = "COMPATIBLE"
    EXPERIMENTAL = "EXPERIMENTAL"
    FAILED = "FAILED"


@dataclass(frozen=True)
class SpecificationViolation:
    rule_id: str
    code: str
    severity: ViolationSeverity
    category: ViolationCategory
    object_id: str
    object_type: str
    expected: Any
    actual: Any
    message: str
    trace_path: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["severity"] = self.severity.value
        result["category"] = self.category.value
        result["trace_path"] = list(self.trace_path)
        return result


@dataclass(frozen=True)
class ConformanceReport:
    spec_version: str
    generated_at: datetime
    object_count: int
    relationship_count: int
    valid: bool
    score: float
    violations: tuple[SpecificationViolation, ...]
    summary: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        return {
            "spec_version": self.spec_version,
            "generated_at": self.generated_at.isoformat(),
            "object_count": self.object_count,
            "relationship_count": self.relationship_count,
            "valid": self.valid,
            "score": self.score,
            "violations": [item.to_dict() for item in self.violations],
            "summary": dict(self.summary),
        }

    def to_json(self, *, indent: int | None = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)


@dataclass(frozen=True)
class CertificationReport:
    conformance: ConformanceReport
    level: CertificationLevel

    @property
    def certification_level(self) -> CertificationLevel:
        return self.level

    def __getattr__(self, name: str) -> Any:
        """Expose required report fields without duplicating conformance state."""
        if name in {
            "spec_version", "generated_at", "object_count", "relationship_count",
            "valid", "score", "violations", "summary",
        }:
            return getattr(self.conformance, name)
        raise AttributeError(name)

    def to_dict(self) -> dict[str, Any]:
        return {**self.conformance.to_dict(), "certification_level": self.level.value}

    def to_json(self, *, indent: int | None = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)


Severity = ViolationSeverity
Category = ViolationCategory
