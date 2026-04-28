from __future__ import annotations

import math

from weather_comparison_engine.schemas.training_sample import TrainingSample
from weather_comparison_engine.validation.quality_reports import (
    build_family_rollout_summary,
    build_family_rollout_trend_summary,
    build_family_rollout_watchlist,
    build_governance_summary,
)


class CalibrationEvaluator:
    def evaluate(
        self,
        samples: list[TrainingSample],
        *,
        probability_field: str = "model_probability",
        bucket_count: int = 10,
    ) -> dict:
        labeled = [
            sample
            for sample in samples
            if sample.outcome in {"YES", "NO"} and _valid_probability(_sample_probability(sample, probability_field))
        ]

        if not labeled:
            return {
                "sample_count": 0,
                "bucket_count": bucket_count,
                "probability_field": probability_field,
                "brier_score": None,
                "log_loss": None,
                "calibration_error": None,
                "hit_rate": None,
                "reliability_curve": [],
                "governance_summary": build_governance_summary(samples),
                "family_rollout_summary": build_family_rollout_summary(
                    samples,
                    probability_field=probability_field,
                ),
                "family_rollout_trend_summary": build_family_rollout_trend_summary(
                    samples,
                    probability_field=probability_field,
                ),
                "family_rollout_watchlist": build_family_rollout_watchlist(
                    samples,
                    probability_field=probability_field,
                ),
            }

        rows = [
            {
                "p": float(_sample_probability(sample, probability_field)),
                "y": 1 if sample.outcome == "YES" else 0,
            }
            for sample in labeled
        ]

        brier = sum((row["p"] - row["y"]) ** 2 for row in rows) / len(rows)
        log_loss = sum(_log_loss_term(row["y"], row["p"]) for row in rows) / len(rows)
        hit_rate = sum((1 if row["p"] >= 0.5 else 0) == row["y"] for row in rows) / len(rows)

        curve = _build_reliability_curve(rows, bucket_count=bucket_count)
        calibration_error = 0.0
        for bucket in curve:
            calibration_error += (
                (bucket["count"] / len(rows))
                * abs(bucket["avg_probability"] - bucket["empirical_yes_rate"])
            )

        return {
            "sample_count": len(rows),
            "bucket_count": bucket_count,
            "probability_field": probability_field,
            "brier_score": round(brier, 6),
            "log_loss": round(log_loss, 6),
            "calibration_error": round(calibration_error, 6),
            "hit_rate": round(hit_rate, 6),
            "reliability_curve": curve,
            "governance_summary": build_governance_summary(samples),
            "family_rollout_summary": build_family_rollout_summary(
                samples,
                probability_field=probability_field,
            ),
            "family_rollout_trend_summary": build_family_rollout_trend_summary(
                samples,
                probability_field=probability_field,
            ),
            "family_rollout_watchlist": build_family_rollout_watchlist(
                samples,
                probability_field=probability_field,
            ),
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


def _log_loss_term(y_true: int, probability: float) -> float:
    p = min(max(probability, 1e-6), 1 - 1e-6)
    return -(y_true * math.log(p) + (1 - y_true) * math.log(1 - p))


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
