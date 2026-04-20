from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from weather_comparison_engine.probability.contract_policy import ProbabilityContractPolicy
from weather_comparison_engine.schemas.training_sample import TrainingSample
from weather_comparison_engine.probability.promotion_policy import PromotionPolicy
from weather_comparison_engine.validation.backtester import Backtester
from weather_comparison_engine.validation.calibration_evaluator import CalibrationEvaluator


def load_training_samples_jsonl(path: str | Path) -> list[TrainingSample]:
    src = Path(path)
    if not src.exists():
        raise FileNotFoundError(f"Missing training samples: {src}")

    text = src.read_text(encoding="utf-8").strip()
    if not text:
        return []

    samples: list[TrainingSample] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        samples.append(TrainingSample.model_validate(json.loads(line)))
    return samples


def build_model_validation_report(
    samples: list[TrainingSample],
    *,
    calibration_bucket_count: int = 10,
    edge_threshold: float = 0.05,
) -> tuple[dict, dict, dict]:
    calibration_evaluator = CalibrationEvaluator()
    backtester = Backtester()

    model_calibration = calibration_evaluator.evaluate(
        samples,
        probability_field="model_probability",
        bucket_count=calibration_bucket_count,
    )
    market_baseline = calibration_evaluator.evaluate(
        samples,
        probability_field="market_probability",
        bucket_count=calibration_bucket_count,
    )
    backtest_report = backtester.run(samples, edge_threshold=edge_threshold)
    family_validation = _family_validation(
        samples,
        calibration_evaluator=calibration_evaluator,
        backtester=backtester,
        calibration_bucket_count=calibration_bucket_count,
        edge_threshold=edge_threshold,
    )
    edge_deciles = _edge_deciles(samples)
    resolver_quality = _resolver_quality(samples)

    labeled_samples = [sample for sample in samples if sample.is_labeled]
    time_values = sorted(sample.timestamp for sample in samples if sample.timestamp)
    family_counts: dict[str, int] = {}
    for sample in samples:
        family = sample.market_family or "unknown"
        family_counts[family] = family_counts.get(family, 0) + 1

    validation_report = {
        "schema_version": "model_validation_report.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model_id": "heuristic_shadow_probability_v1",
        "model_type": "probability_shadow",
        "deployment_mode": "shadow",
        "approved_for_live": False,
        "calibration_status": "not_calibrated",
        "sample_count": len(samples),
        "labeled_sample_count": len(labeled_samples),
        "training_data_range": (
            f"{time_values[0]}/{time_values[-1]}" if time_values else None
        ),
        "market_family_counts": family_counts,
        "validation_metrics": {
            "brier_score": model_calibration.get("brier_score"),
            "log_loss": model_calibration.get("log_loss"),
            "calibration_error": model_calibration.get("calibration_error"),
            "market_baseline_brier_score": market_baseline.get("brier_score"),
            "market_baseline_log_loss": market_baseline.get("log_loss"),
            "roi_backtest": backtest_report.get("roi"),
            "max_drawdown": backtest_report.get("max_drawdown"),
            "hit_rate": backtest_report.get("hit_rate"),
        },
        "family_validation": family_validation,
        "edge_deciles": edge_deciles,
        "resolver_quality": resolver_quality,
        "note": (
            "Phase 8 validation is evaluating the current heuristic shadow probability and "
            "edge-based decision scaffold. Outputs are for offline validation only."
        ),
    }

    contract = ProbabilityContractPolicy().evaluate(validation_report)
    validation_report["calibration_status"] = contract["calibration_status"]
    validation_report["approved_for_live"] = contract["approved_for_live"]
    validation_report["deployment_mode"] = contract["deployment_mode"]
    validation_report["probability_mode"] = contract["probability_mode"]
    validation_report["execution_constraint"] = contract["execution_constraint"]
    validation_report["promotion_reason"] = contract["promotion_reason"]
    validation_report["contract_source"] = contract["contract_source"]
    validation_report["contract_checks"] = contract["contract_checks"]

    promotion_state = PromotionPolicy().evaluate(validation_report=validation_report)
    validation_report["promotion_state"] = promotion_state
    validation_report["base_probability_mode"] = promotion_state["base_probability_mode"]
    validation_report["base_execution_constraint"] = promotion_state["base_execution_constraint"]
    validation_report["demotion_reason"] = promotion_state["demotion_reason"]
    validation_report["promotion_policy_version"] = promotion_state["promotion_policy_version"]
    validation_report["promotion_blockers"] = promotion_state["blockers"]

    calibration_report = {
        "schema_version": "calibration_report.v1",
        "generated_at": validation_report["generated_at"],
        "model_probability": model_calibration,
        "market_probability_baseline": market_baseline,
    }

    return calibration_report, backtest_report, validation_report


def _family_validation(
    samples: list[TrainingSample],
    *,
    calibration_evaluator: CalibrationEvaluator,
    backtester: Backtester,
    calibration_bucket_count: int,
    edge_threshold: float,
) -> dict[str, dict]:
    by_family: dict[str, list[TrainingSample]] = {}
    for sample in samples:
        family = sample.market_family or "unknown"
        by_family.setdefault(family, []).append(sample)

    result: dict[str, dict] = {}
    for family, family_samples in sorted(by_family.items()):
        calibration = calibration_evaluator.evaluate(
            family_samples,
            probability_field="model_probability",
            bucket_count=calibration_bucket_count,
        )
        backtest = backtester.run(family_samples, edge_threshold=edge_threshold)
        result[family] = {
            "sample_count": len(family_samples),
            "labeled_sample_count": len([sample for sample in family_samples if sample.is_labeled]),
            "brier_score": calibration.get("brier_score"),
            "log_loss": calibration.get("log_loss"),
            "calibration_error": calibration.get("calibration_error"),
            "trade_count": backtest.get("trade_count"),
            "roi": backtest.get("roi"),
            "hit_rate": backtest.get("hit_rate"),
        }
    return result


def _edge_deciles(samples: list[TrainingSample]) -> list[dict]:
    ranked = [
        sample
        for sample in samples
        if sample.is_labeled and _sample_edge(sample) is not None and sample.outcome in {"YES", "NO"}
    ]
    if not ranked:
        return []

    ranked.sort(key=lambda sample: float(_sample_edge(sample) or 0.0))
    bucket_count = min(10, len(ranked))
    buckets: list[list[TrainingSample]] = [[] for _ in range(bucket_count)]

    for idx, sample in enumerate(ranked):
        bucket_index = min((idx * bucket_count) // len(ranked), bucket_count - 1)
        buckets[bucket_index].append(sample)

    rows: list[dict] = []
    for idx, bucket in enumerate(buckets):
        if not bucket:
            continue
        edges = [float(_sample_edge(sample) or 0.0) for sample in bucket]
        yes_rate = sum(1 for sample in bucket if sample.outcome == "YES") / len(bucket)
        rows.append(
            {
                "decile": idx + 1,
                "count": len(bucket),
                "min_edge": round(min(edges), 6),
                "max_edge": round(max(edges), 6),
                "avg_edge": round(sum(edges) / len(edges), 6),
                "yes_rate": round(yes_rate, 6),
            }
        )
    return rows


def _sample_edge(sample: TrainingSample) -> float | None:
    if sample.edge is not None:
        return float(sample.edge)
    if sample.model_probability is not None and sample.market_probability is not None:
        return float(sample.model_probability) - float(sample.market_probability)
    return None


def _resolver_quality(samples: list[TrainingSample]) -> dict:
    total = len(samples)
    if total == 0:
        return {
            "sample_count": 0,
            "matched_count": 0,
            "unmatched_count": 0,
            "resolver_match_rate": None,
            "unmatched_market_rate": None,
            "resolver_status_counts": {},
        }

    counts: dict[str, int] = {}
    for sample in samples:
        status = sample.resolver_status or "unknown"
        counts[status] = counts.get(status, 0) + 1

    matched_count = counts.get("matched", 0)
    unmatched_count = total - matched_count

    return {
        "sample_count": total,
        "matched_count": matched_count,
        "unmatched_count": unmatched_count,
        "resolver_match_rate": round(matched_count / total, 6),
        "unmatched_market_rate": round(unmatched_count / total, 6),
        "resolver_status_counts": counts,
    }
