from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from .models import (
    CertificationLevel,
    CertificationReport,
    ConformanceReport,
    SpecificationViolation,
    ViolationSeverity,
)


PENALTIES = {
    ViolationSeverity.ERROR: 25.0,
    ViolationSeverity.WARNING: 8.0,
    ViolationSeverity.INFO: 2.0,
}


def build_conformance_report(
    *,
    spec_version: str,
    object_count: int,
    relationship_count: int,
    violations: Iterable[SpecificationViolation],
) -> ConformanceReport:
    ordered = tuple(sorted(violations, key=lambda v: (v.object_id, v.rule_id, v.code, v.trace_path)))
    counts = {severity.value: 0 for severity in ViolationSeverity}
    for violation in ordered:
        counts[violation.severity.value] += 1
    score = max(0.0, 100.0 - sum(PENALTIES[v.severity] for v in ordered))
    return ConformanceReport(
        spec_version=spec_version,
        generated_at=datetime.now(timezone.utc),
        object_count=object_count,
        relationship_count=relationship_count,
        valid=counts[ViolationSeverity.ERROR.value] == 0,
        score=score,
        violations=ordered,
        summary={"error_count": counts["ERROR"], "warning_count": counts["WARNING"], "info_count": counts["INFO"]},
    )


def certification_level(report: ConformanceReport) -> CertificationLevel:
    if not report.valid:
        return CertificationLevel.FAILED
    if not report.violations:
        return CertificationLevel.CERTIFIED
    if report.score >= 80:
        return CertificationLevel.COMPATIBLE
    return CertificationLevel.EXPERIMENTAL


def certify_report(report: ConformanceReport) -> CertificationReport:
    return CertificationReport(report, certification_level(report))
