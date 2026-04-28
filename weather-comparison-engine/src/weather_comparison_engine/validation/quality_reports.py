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


def build_governance_summary(samples: list[TrainingSample]) -> dict:
    total = len(samples)
    if total == 0:
        return {
            "sample_count": 0,
            "canonical_sample_count": 0,
            "source_policy_sample_count": 0,
            "normalization_version_counts": {},
            "source_policy_ref_counts": {},
            "precision_policy_ref_counts": {},
            "rounding_policy_ref_counts": {},
            "band_mapping_policy_ref_counts": {},
            "freshness_status_counts": {},
            "source_match_grade_counts": {},
            "canonical_ratio": None,
            "source_policy_coverage": None,
            "normalization_coverage": None,
        }

    canonical_sample_count = 0
    source_policy_sample_count = 0
    normalization_version_counts: dict[str, int] = {}
    source_policy_ref_counts: dict[str, int] = {}
    precision_policy_ref_counts: dict[str, int] = {}
    rounding_policy_ref_counts: dict[str, int] = {}
    band_mapping_policy_ref_counts: dict[str, int] = {}
    freshness_status_counts: dict[str, int] = {}
    source_match_grade_counts: dict[str, int] = {}

    for sample in samples:
        if sample.canonical_value is not None and sample.canonical_unit not in (None, ""):
            canonical_sample_count += 1
        if sample.source_policy_ref not in (None, ""):
            source_policy_sample_count += 1

        _increment_count(normalization_version_counts, sample.normalization_version or "unknown")
        _increment_count(source_policy_ref_counts, sample.source_policy_ref or "unknown")
        _increment_count(precision_policy_ref_counts, sample.precision_policy_ref or "unknown")
        _increment_count(rounding_policy_ref_counts, sample.rounding_policy_ref or "unknown")
        _increment_count(band_mapping_policy_ref_counts, sample.band_mapping_policy_ref or "unknown")
        _increment_count(freshness_status_counts, sample.freshness_status or "unknown")
        _increment_count(source_match_grade_counts, sample.source_match_grade or "unknown")

    return {
        "sample_count": total,
        "canonical_sample_count": canonical_sample_count,
        "source_policy_sample_count": source_policy_sample_count,
        "normalization_version_counts": normalization_version_counts,
        "source_policy_ref_counts": source_policy_ref_counts,
        "precision_policy_ref_counts": precision_policy_ref_counts,
        "rounding_policy_ref_counts": rounding_policy_ref_counts,
        "band_mapping_policy_ref_counts": band_mapping_policy_ref_counts,
        "freshness_status_counts": freshness_status_counts,
        "source_match_grade_counts": source_match_grade_counts,
        "canonical_ratio": round(canonical_sample_count / total, 6),
        "source_policy_coverage": round(source_policy_sample_count / total, 6),
        "normalization_coverage": round(
            sum(1 for sample in samples if sample.normalization_version not in (None, ""))
            / total,
            6,
        ),
    }


def build_family_rollout_summary(
    samples: list[TrainingSample],
    *,
    probability_field: str = "model_probability",
    drift_bucket_thresholds: tuple[float, float] = (0.02, 0.05),
    ready_family_min_labeled_rows: int = 2,
) -> dict:
    total = len(samples)
    family_buckets: dict[str, list[TrainingSample]] = {}
    for sample in samples:
        family = sample.market_family or "unknown"
        family_buckets.setdefault(family, []).append(sample)

    family_counts = {family: len(bucket) for family, bucket in sorted(family_buckets.items())}
    labeled_family_counts = {
        family: len([sample for sample in bucket if sample.is_labeled])
        for family, bucket in sorted(family_buckets.items())
    }

    family_count = len(family_counts)
    covered_family_count = sum(1 for count in labeled_family_counts.values() if count > 0)
    ready_family_count = sum(1 for count in labeled_family_counts.values() if count >= ready_family_min_labeled_rows)

    global_stats = _calibration_stats(samples, probability_field=probability_field)
    family_summaries: list[dict] = []
    drift_bucket_counts = {"low": 0, "medium": 0, "high": 0}

    for family, bucket in sorted(family_buckets.items()):
        family_stats = _calibration_stats(bucket, probability_field=probability_field)
        drift_from_global = None
        if family_stats["calibration_error"] is not None and global_stats["calibration_error"] is not None:
            drift_from_global = round(
                abs(float(family_stats["calibration_error"]) - float(global_stats["calibration_error"])),
                6,
            )
            _increment_drift_bucket_counts(drift_bucket_counts, drift_from_global, thresholds=drift_bucket_thresholds)
        family_summaries.append(
            {
                "market_family": family,
                "sample_count": len(bucket),
                "labeled_sample_count": len([sample for sample in bucket if sample.is_labeled]),
                "coverage_status": _family_coverage_status(
                    len([sample for sample in bucket if sample.is_labeled]),
                    ready_family_min_labeled_rows=ready_family_min_labeled_rows,
                ),
                "brier_score": family_stats["brier_score"],
                "calibration_error": family_stats["calibration_error"],
                "drift_from_global": drift_from_global,
                "drift_bucket": _family_drift_bucket(drift_from_global, thresholds=drift_bucket_thresholds),
            }
        )

    top_family = None
    if family_summaries:
        top_family = max(family_summaries, key=lambda row: int(row.get("sample_count") or 0))
    top_drift_family = None
    drift_candidates = [row for row in family_summaries if row.get("drift_from_global") is not None]
    if drift_candidates:
        drift_candidates.sort(key=lambda row: float(row.get("drift_from_global") or 0.0), reverse=True)
        top_drift_family = drift_candidates[0]

    return {
        "schema_version": "family_rollout_summary.v1",
        "sample_count": total,
        "probability_field": probability_field,
        "family_count": family_count,
        "covered_family_count": covered_family_count,
        "ready_family_count": ready_family_count,
        "coverage_ratio": round(covered_family_count / family_count, 6) if family_count else None,
        "ready_ratio": round(ready_family_count / family_count, 6) if family_count else None,
        "family_counts": family_counts,
        "labeled_family_counts": labeled_family_counts,
        "global_brier_score": global_stats["brier_score"],
        "global_calibration_error": global_stats["calibration_error"],
        "family_summaries": family_summaries,
        "top_family": top_family.get("market_family") if top_family else None,
        "top_family_sample_count": top_family.get("sample_count") if top_family else None,
        "top_drift_family": top_drift_family.get("market_family") if top_drift_family else None,
        "top_drift_value": top_drift_family.get("drift_from_global") if top_drift_family else None,
        "drift_bucket_counts": drift_bucket_counts,
    }


def build_family_rollout_trend_summary(
    samples: list[TrainingSample],
    *,
    probability_field: str = "model_probability",
    bucket_count: int = 3,
    drift_bucket_thresholds: tuple[float, float] = (0.02, 0.05),
    ready_family_min_labeled_rows: int = 2,
) -> dict:
    total = len(samples)
    if total == 0:
        return {
            "schema_version": "family_rollout_trend_summary.v1",
            "sample_count": 0,
            "bucket_count": bucket_count,
            "trend_windows": [],
            "coverage_movement": None,
            "ready_movement": None,
            "drift_movement": None,
        }

    sorted_samples = sorted(
        samples,
        key=lambda sample: _parse_iso(sample.timestamp) or datetime.min.replace(tzinfo=timezone.utc),
    )
    window_count = max(1, min(bucket_count, total))
    windows = _chunk_samples(sorted_samples, window_count)

    trend_windows: list[dict] = []
    for idx, window in enumerate(windows):
        rollout = build_family_rollout_summary(
            window,
            probability_field=probability_field,
            drift_bucket_thresholds=drift_bucket_thresholds,
            ready_family_min_labeled_rows=ready_family_min_labeled_rows,
        )
        timestamps = [_parse_iso(sample.timestamp) for sample in window if _parse_iso(sample.timestamp)]
        trend_windows.append(
            {
                "window_index": idx + 1,
                "window_label": f"window_{idx + 1}",
                "start_timestamp": timestamps[0].isoformat() if timestamps else None,
                "end_timestamp": timestamps[-1].isoformat() if timestamps else None,
                "sample_count": len(window),
                "family_count": rollout.get("family_count"),
                "coverage_ratio": rollout.get("coverage_ratio"),
                "ready_ratio": rollout.get("ready_ratio"),
                "top_family": rollout.get("top_family"),
                "top_drift_family": rollout.get("top_drift_family"),
                "top_drift_value": rollout.get("top_drift_value"),
                "drift_bucket_counts": rollout.get("drift_bucket_counts"),
            }
        )

    first_window = trend_windows[0] if trend_windows else {}
    last_window = trend_windows[-1] if trend_windows else {}
    coverage_movement = _numeric_delta(
        last_window.get("coverage_ratio"),
        first_window.get("coverage_ratio"),
    )
    ready_movement = _numeric_delta(
        last_window.get("ready_ratio"),
        first_window.get("ready_ratio"),
    )
    drift_movement = _numeric_delta(
        last_window.get("top_drift_value"),
        first_window.get("top_drift_value"),
    )

    return {
        "schema_version": "family_rollout_trend_summary.v1",
        "sample_count": total,
        "bucket_count": window_count,
        "trend_windows": trend_windows,
        "coverage_movement": coverage_movement,
        "ready_movement": ready_movement,
        "drift_movement": drift_movement,
    }


def build_family_rollout_watchlist(
    samples: list[TrainingSample],
    *,
    probability_field: str = "model_probability",
    drift_bucket_thresholds: tuple[float, float] = (0.02, 0.05),
    ready_family_min_labeled_rows: int = 2,
) -> dict:
    total = len(samples)
    if total == 0:
        return {
            "schema_version": "family_rollout_watchlist.v1",
            "sample_count": 0,
            "probability_field": probability_field,
            "family_count": 0,
            "watchlist_count": 0,
            "stalled_family_count": 0,
            "drift_spike_family_count": 0,
            "expansion_backlog_count": 0,
            "watchlist": [],
            "top_watchlist_family": None,
            "top_watchlist_reason": None,
            "top_watchlist_attention_level": None,
            "top_watchlist_sample_count": None,
        }

    rollout = build_family_rollout_summary(
        samples,
        probability_field=probability_field,
        drift_bucket_thresholds=drift_bucket_thresholds,
        ready_family_min_labeled_rows=ready_family_min_labeled_rows,
    )

    watchlist: list[dict] = []
    stalled_family_count = 0
    drift_spike_family_count = 0
    expansion_backlog_count = 0

    for idx, family_row in enumerate(rollout.get("family_summaries") or [], start=1):
        if not isinstance(family_row, dict):
            continue

        coverage_status = str(family_row.get("coverage_status") or "unknown")
        drift_bucket = str(family_row.get("drift_bucket") or "unknown")
        drift_from_global = family_row.get("drift_from_global")
        sample_count = int(family_row.get("sample_count") or 0)
        labeled_sample_count = int(family_row.get("labeled_sample_count") or 0)

        is_stalled = coverage_status != "healthy"
        is_drift_spike = drift_bucket == "high"
        is_expansion_backlog = coverage_status == "blocked"

        if is_stalled:
            stalled_family_count += 1
        if is_drift_spike:
            drift_spike_family_count += 1
        if is_expansion_backlog:
            expansion_backlog_count += 1

        attention_level = _family_watchlist_attention_level(
            coverage_status=coverage_status,
            drift_bucket=drift_bucket,
        )
        watchlist_reason = _family_watchlist_reason(
            coverage_status=coverage_status,
            drift_bucket=drift_bucket,
            drift_from_global=drift_from_global,
        )
        suggested_action = _family_watchlist_action(
            coverage_status=coverage_status,
            drift_bucket=drift_bucket,
        )
        watchlist.append(
            {
                "watchlist_rank": idx,
                "market_family": family_row.get("market_family"),
                "sample_count": sample_count,
                "labeled_sample_count": labeled_sample_count,
                "coverage_status": coverage_status,
                "calibration_error": family_row.get("calibration_error"),
                "drift_from_global": drift_from_global,
                "drift_bucket": drift_bucket,
                "attention_level": attention_level,
                "watchlist_reason": watchlist_reason,
                "suggested_action": suggested_action,
                "is_stalled": is_stalled,
                "is_drift_spike": is_drift_spike,
                "is_expansion_backlog": is_expansion_backlog,
            }
        )

    watchlist.sort(
        key=lambda row: (
            _attention_level_rank(str(row.get("attention_level") or "low")),
            -float(row.get("drift_from_global") or 0.0),
            -int(row.get("sample_count") or 0),
            str(row.get("market_family") or ""),
        )
    )
    for idx, row in enumerate(watchlist, start=1):
        row["watchlist_rank"] = idx

    top_watchlist = watchlist[0] if watchlist else {}
    return {
        "schema_version": "family_rollout_watchlist.v1",
        "sample_count": total,
        "probability_field": probability_field,
        "family_count": int(rollout.get("family_count") or 0),
        "watchlist_count": len(watchlist),
        "stalled_family_count": stalled_family_count,
        "drift_spike_family_count": drift_spike_family_count,
        "expansion_backlog_count": expansion_backlog_count,
        "watchlist": watchlist,
        "top_watchlist_family": top_watchlist.get("market_family"),
        "top_watchlist_reason": top_watchlist.get("watchlist_reason"),
        "top_watchlist_attention_level": top_watchlist.get("attention_level"),
        "top_watchlist_sample_count": top_watchlist.get("sample_count"),
    }


def build_validation_assimilation_summary(
    samples: list[TrainingSample],
    *,
    validation_report: dict | None = None,
    label_coverage_report: dict | None = None,
    backtest_report: dict | None = None,
    source_policy_status: dict | None = None,
) -> dict:
    report = validation_report or {}
    governance = report.get("governance_summary") or {}
    rollout = report.get("family_rollout_summary") or {}
    trend = report.get("family_rollout_trend_summary") or {}
    watchlist = report.get("family_rollout_watchlist") or {}
    coverage = label_coverage_report or {}

    sample_count = len(samples)
    labeled_sample_count = len([sample for sample in samples if sample.is_labeled])
    canonical_sample_count = int(governance.get("canonical_sample_count") or 0)
    source_policy_sample_count = int(governance.get("source_policy_sample_count") or 0)
    canonical_ratio = governance.get("canonical_ratio")
    source_policy_coverage = governance.get("source_policy_coverage")
    normalization_coverage = governance.get("normalization_coverage")
    labeled_ratio = coverage.get("labeled_ratio")
    if coverage.get("status") is not None:
        label_status = str(coverage.get("status") or "unknown").lower()
    elif labeled_sample_count > 0:
        label_status = "healthy"
    else:
        label_status = "missing"

    feature_store_ready = _ratio_ready(canonical_ratio) and _ratio_ready(source_policy_coverage) and _ratio_ready(normalization_coverage)
    label_store_ready = label_status in {"healthy", "ok"} and labeled_sample_count > 0
    backtest_ready = int((backtest_report or {}).get("trade_count") or 0) > 0

    blockers: list[str] = []
    if not _ratio_ready(canonical_ratio):
        blockers.append("canonical_coverage_below_1")
    if not _ratio_ready(source_policy_coverage):
        blockers.append("source_policy_coverage_below_1")
    if not _ratio_ready(normalization_coverage):
        blockers.append("normalization_coverage_below_1")
    if label_status not in {"healthy", "ok"}:
        blockers.append(f"label_coverage:{label_status}")
    if str(report.get("calibration_status") or "").lower() not in {"calibrated", "live_approved"}:
        blockers.append(f"calibration:{report.get('calibration_status') or 'unknown'}")
    if not rollout.get("family_count"):
        blockers.append("family_rollout_missing")

    if blockers:
        assimilation_status = "blocked"
    elif feature_store_ready and label_store_ready:
        assimilation_status = "healthy"
    else:
        assimilation_status = "warning"

    if source_policy_status and str(source_policy_status.get("overall_status") or "").lower() not in {"healthy", "ok"}:
        blockers.append(f"source_policy:{source_policy_status.get('overall_status') or 'unknown'}")
        assimilation_status = "blocked"

    primary_blocker = blockers[0] if blockers else "none"
    summary_line = _validation_assimilation_summary_line(
        assimilation_status=assimilation_status,
        primary_blocker=primary_blocker,
        top_family=rollout.get("top_family"),
        top_watchlist_family=watchlist.get("top_watchlist_family"),
    )

    return {
        "schema_version": "validation_assimilation_summary.v1",
        "sample_count": sample_count,
        "labeled_sample_count": labeled_sample_count,
        "canonical_sample_count": canonical_sample_count,
        "source_policy_sample_count": source_policy_sample_count,
        "canonical_ratio": canonical_ratio,
        "source_policy_coverage": source_policy_coverage,
        "normalization_coverage": normalization_coverage,
        "labeled_ratio": labeled_ratio,
        "validation_status": label_status,
        "feature_store_ready": feature_store_ready,
        "label_store_ready": label_store_ready,
        "backtest_ready": backtest_ready,
        "family_count": rollout.get("family_count"),
        "ready_family_count": rollout.get("ready_family_count"),
        "coverage_ratio": rollout.get("coverage_ratio"),
        "ready_ratio": rollout.get("ready_ratio"),
        "top_family": rollout.get("top_family"),
        "top_drift_family": rollout.get("top_drift_family"),
        "top_drift_value": rollout.get("top_drift_value"),
        "drift_movement": trend.get("drift_movement"),
        "watchlist_count": watchlist.get("watchlist_count"),
        "stalled_family_count": watchlist.get("stalled_family_count"),
        "drift_spike_family_count": watchlist.get("drift_spike_family_count"),
        "expansion_backlog_count": watchlist.get("expansion_backlog_count"),
        "top_watchlist_family": watchlist.get("top_watchlist_family"),
        "top_watchlist_attention_level": watchlist.get("top_watchlist_attention_level"),
        "top_watchlist_reason": watchlist.get("top_watchlist_reason"),
        "blockers": blockers,
        "primary_blocker": primary_blocker,
        "assimilation_status": assimilation_status,
        "summary_line": summary_line,
    }


def _increment_count(counter: dict[str, int], key: str) -> None:
    counter[key] = counter.get(key, 0) + 1


def _calibration_stats(samples: list[TrainingSample], *, probability_field: str) -> dict:
    rows = [
        {
            "p": float(_sample_probability(sample, probability_field)),
            "y": 1 if sample.outcome == "YES" else 0,
        }
        for sample in samples
        if sample.outcome in {"YES", "NO"} and _valid_probability(_sample_probability(sample, probability_field))
    ]
    if not rows:
        return {
            "sample_count": 0,
            "brier_score": None,
            "calibration_error": None,
        }

    brier = sum((row["p"] - row["y"]) ** 2 for row in rows) / len(rows)
    curve = _build_reliability_curve(rows, bucket_count=min(10, max(1, len(rows))))
    calibration_error = 0.0
    for bucket in curve:
        calibration_error += (
            (bucket["count"] / len(rows))
            * abs(bucket["avg_probability"] - bucket["empirical_yes_rate"])
        )
    return {
        "sample_count": len(rows),
        "brier_score": round(brier, 6),
        "calibration_error": round(calibration_error, 6),
    }


def _build_reliability_curve(rows: list[dict], *, bucket_count: int) -> list[dict]:
    buckets: list[list[dict]] = [[] for _ in range(bucket_count)]
    for row in rows:
        idx = min(int(row["p"] * bucket_count), bucket_count - 1)
        buckets[idx].append(row)

    curve: list[dict] = []
    for idx, bucket in enumerate(buckets):
        if not bucket:
            continue
        lower = idx / bucket_count
        upper = (idx + 1) / bucket_count
        avg_probability = sum(row["p"] for row in bucket) / len(bucket)
        empirical_yes_rate = sum(row["y"] for row in bucket) / len(bucket)
        curve.append(
            {
                "bucket": idx,
                "bucket_start": round(lower, 6),
                "bucket_end": round(upper, 6),
                "count": len(bucket),
                "avg_probability": round(avg_probability, 6),
                "empirical_yes_rate": round(empirical_yes_rate, 6),
            }
        )
    return curve


def _valid_probability(value: object) -> bool:
    try:
        if value is None:
            return False
        number = float(value)
    except (TypeError, ValueError):
        return False
    return 0.0 <= number <= 1.0


def _sample_probability(sample: TrainingSample, probability_field: str) -> float | None:
    value = getattr(sample, probability_field, None)
    if value is not None:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
    fallback = getattr(sample, "model_value", None)
    try:
        return float(fallback) if fallback is not None else None
    except (TypeError, ValueError):
        return None


def _family_coverage_status(labeled_rows: int, *, ready_family_min_labeled_rows: int) -> str:
    if labeled_rows >= ready_family_min_labeled_rows:
        return "healthy"
    if labeled_rows > 0:
        return "warning"
    return "blocked"


def _family_drift_bucket(value: float | None, *, thresholds: tuple[float, float]) -> str:
    if value is None:
        return "low"
    low_threshold, high_threshold = thresholds
    if value >= high_threshold:
        return "high"
    if value >= low_threshold:
        return "medium"
    return "low"


def _increment_drift_bucket_counts(
    counter: dict[str, int],
    value: float,
    *,
    thresholds: tuple[float, float],
) -> None:
    bucket = _family_drift_bucket(value, thresholds=thresholds)
    counter[bucket] = counter.get(bucket, 0) + 1


def _chunk_samples(samples: list[TrainingSample], bucket_count: int) -> list[list[TrainingSample]]:
    buckets: list[list[TrainingSample]] = [[] for _ in range(bucket_count)]
    if not samples:
        return buckets
    for idx, sample in enumerate(samples):
        bucket_index = min((idx * bucket_count) // len(samples), bucket_count - 1)
        buckets[bucket_index].append(sample)
    return [bucket for bucket in buckets if bucket]


def _numeric_delta(end: object, start: object) -> float | None:
    try:
        if end is None or start is None:
            return None
        return round(float(end) - float(start), 6)
    except (TypeError, ValueError):
        return None


def _family_watchlist_attention_level(*, coverage_status: str, drift_bucket: str) -> str:
    if coverage_status == "blocked" and drift_bucket == "high":
        return "critical"
    if coverage_status == "blocked" or drift_bucket == "high":
        return "high"
    if coverage_status == "warning" or drift_bucket == "medium":
        return "medium"
    return "low"


def _attention_level_rank(attention_level: str) -> int:
    return {
        "critical": 0,
        "high": 1,
        "medium": 2,
        "low": 3,
    }.get(attention_level, 4)


def _ratio_ready(value: object) -> bool:
    try:
        if value is None:
            return False
        return float(value) >= 1.0
    except (TypeError, ValueError):
        return False


def _validation_assimilation_summary_line(
    *,
    assimilation_status: str,
    primary_blocker: str,
    top_family: object,
    top_watchlist_family: object,
) -> str:
    if assimilation_status == "blocked":
        return f"Validation assimilation blocked; review {primary_blocker}"
    focus = top_watchlist_family or top_family or "validation"
    if assimilation_status == "warning":
        return f"Validation assimilation warming; review {focus}"
    return f"Validation assimilation healthy; focus {focus}"


def _family_watchlist_reason(
    *,
    coverage_status: str,
    drift_bucket: str,
    drift_from_global: float | None,
) -> str:
    reasons: list[str] = []
    if coverage_status == "blocked":
        reasons.append("coverage_stalled")
    elif coverage_status == "warning":
        reasons.append("coverage_aging")
    if drift_bucket == "high":
        reasons.append("drift_spike")
    elif drift_bucket == "medium":
        reasons.append("drift_watch")
    if drift_from_global is not None:
        reasons.append(f"drift={round(float(drift_from_global), 6)}")
    return "+".join(reasons) or "watchlist_candidate"


def _family_watchlist_action(*, coverage_status: str, drift_bucket: str) -> str:
    if coverage_status == "blocked" and drift_bucket == "high":
        return "prioritize_backfill_and_resolver_review"
    if coverage_status == "blocked":
        return "prioritize_family_backfill"
    if drift_bucket == "high":
        return "review_drift_spike"
    if coverage_status == "warning" or drift_bucket == "medium":
        return "watch_and_backfill"
    return "monitor"
