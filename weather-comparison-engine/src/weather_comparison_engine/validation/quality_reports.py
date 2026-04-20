from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from weather_comparison_engine.schemas.training_sample import TrainingSample
from weather_comparison_engine.settings import (
    VALIDATION_FRESHNESS_WARNING_AFTER_SECONDS,
    VALIDATION_LABEL_COVERAGE_MIN_FAMILY_LABELED_ROWS,
    VALIDATION_LABEL_COVERAGE_MIN_LABELED_ROWS,
    VALIDATION_LABEL_COVERAGE_MIN_RATIO,
    VALIDATION_MONITOR_STALE_AFTER_SECONDS,
)


class ValidationQualityReportBuilder:
    def __init__(self, *, now: datetime | None = None) -> None:
        self.now = now or datetime.now(timezone.utc)

    def build_validation_freshness_status(
        self,
        validation_report: dict | None,
        *,
        warning_after_seconds: int | None = None,
        stale_after_seconds: int | None = None,
    ) -> dict:
        warning_after = (
            warning_after_seconds
            if warning_after_seconds is not None
            else VALIDATION_FRESHNESS_WARNING_AFTER_SECONDS
        )
        stale_after = (
            stale_after_seconds
            if stale_after_seconds is not None
            else VALIDATION_MONITOR_STALE_AFTER_SECONDS
        )
        if not validation_report:
            return {
                "schema_version": "validation_freshness_status.v1",
                "generated_at": self.now.isoformat(),
                "status": "missing",
                "validation_generated_at": None,
                "freshness_seconds": None,
                "warning_after_seconds": warning_after,
                "stale_after_seconds": stale_after,
                "probability_mode": "unknown",
                "execution_constraint": "manual_advisory_only",
                "reason": "validation_report_missing",
            }

        generated_at = _parse_iso(validation_report.get("generated_at"))
        if generated_at is None:
            return {
                "schema_version": "validation_freshness_status.v1",
                "generated_at": self.now.isoformat(),
                "status": "warning",
                "validation_generated_at": None,
                "freshness_seconds": None,
                "warning_after_seconds": warning_after,
                "stale_after_seconds": stale_after,
                "probability_mode": str(validation_report.get("probability_mode") or "unknown"),
                "execution_constraint": str(
                    validation_report.get("execution_constraint") or "manual_advisory_only"
                ),
                "reason": "validation_generated_at_missing",
            }

        freshness_seconds = max((self.now - generated_at).total_seconds(), 0.0)
        if freshness_seconds > float(stale_after):
            status = "blocked"
            reason = "validation_report_stale"
        elif freshness_seconds > float(warning_after):
            status = "warning"
            reason = "validation_report_aging"
        else:
            status = "healthy"
            reason = "validation_report_fresh"

        return {
            "schema_version": "validation_freshness_status.v1",
            "generated_at": self.now.isoformat(),
            "status": status,
            "validation_generated_at": generated_at.isoformat(),
            "freshness_seconds": freshness_seconds,
            "warning_after_seconds": warning_after,
            "stale_after_seconds": stale_after,
            "probability_mode": str(validation_report.get("probability_mode") or "unknown"),
            "execution_constraint": str(
                validation_report.get("execution_constraint") or "manual_advisory_only"
            ),
            "reason": reason,
        }

    def build_label_coverage_report(
        self,
        samples: list[TrainingSample],
        *,
        validation_report: dict | None = None,
        official_records: list[dict] | None = None,
        min_labeled_rows: int | None = None,
        min_labeled_ratio: float | None = None,
        min_family_labeled_rows: int | None = None,
    ) -> dict:
        min_rows = (
            min_labeled_rows
            if min_labeled_rows is not None
            else VALIDATION_LABEL_COVERAGE_MIN_LABELED_ROWS
        )
        min_ratio = (
            min_labeled_ratio
            if min_labeled_ratio is not None
            else VALIDATION_LABEL_COVERAGE_MIN_RATIO
        )
        min_family_rows = (
            min_family_labeled_rows
            if min_family_labeled_rows is not None
            else VALIDATION_LABEL_COVERAGE_MIN_FAMILY_LABELED_ROWS
        )

        tracked_rows = len(samples)
        labeled = [sample for sample in samples if sample.is_labeled]
        labeled_rows = len(labeled)
        unlabeled_rows = tracked_rows - labeled_rows
        labeled_ratio = round(labeled_rows / tracked_rows, 6) if tracked_rows else 0.0

        family_coverage = _build_family_coverage(samples, min_family_rows)
        official_source_counts = Counter(
            str(record.get("source") or "unknown") for record in (official_records or [])
        )

        blockers: list[str] = []
        if tracked_rows == 0:
            blockers.append("training_samples_missing")
        if labeled_rows < min_rows:
            blockers.append("labeled_rows_below_min")
        if tracked_rows > 0 and labeled_ratio < float(min_ratio):
            blockers.append("labeled_ratio_below_min")
        for family, payload in family_coverage.items():
            if payload["tracked_rows"] > 0 and payload["labeled_rows"] < min_family_rows:
                blockers.append(f"family:{family}:labeled_rows_below_min")

        status = "healthy"
        if blockers:
            status = "blocked"
        elif tracked_rows and labeled_rows < (min_rows * 2):
            status = "warning"

        return {
            "schema_version": "label_coverage_report.v1",
            "generated_at": self.now.isoformat(),
            "status": status,
            "tracked_rows": tracked_rows,
            "labeled_rows": labeled_rows,
            "unlabeled_rows": unlabeled_rows,
            "labeled_ratio": labeled_ratio,
            "minimum_labeled_rows": min_rows,
            "minimum_labeled_ratio": min_ratio,
            "minimum_family_labeled_rows": min_family_rows,
            "official_record_count": len(official_records or []),
            "validation_sample_count": int(validation_report.get("sample_count") or 0)
            if validation_report
            else tracked_rows,
            "validation_labeled_sample_count": int(validation_report.get("labeled_sample_count") or 0)
            if validation_report
            else labeled_rows,
            "market_family_coverage": family_coverage,
            "official_source_counts": dict(official_source_counts),
            "blockers": blockers,
        }

    def write(self, path: str | Path, payload: dict) -> Path:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return out


def _build_family_coverage(samples: list[TrainingSample], min_family_rows: int) -> dict[str, dict]:
    family_buckets: dict[str, list[TrainingSample]] = {}
    for sample in samples:
        family = sample.market_family or "unknown"
        family_buckets.setdefault(family, []).append(sample)

    coverage: dict[str, dict] = {}
    for family, family_samples in sorted(family_buckets.items()):
        tracked_rows = len(family_samples)
        labeled_rows = len([sample for sample in family_samples if sample.is_labeled])
        ratio = round(labeled_rows / tracked_rows, 6) if tracked_rows else 0.0
        status = "healthy" if labeled_rows >= min_family_rows else "blocked"
        coverage[family] = {
            "tracked_rows": tracked_rows,
            "labeled_rows": labeled_rows,
            "labeled_ratio": ratio,
            "status": status,
        }
    return coverage


def _parse_iso(value: Any) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)
