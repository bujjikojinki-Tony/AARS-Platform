from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from weather_comparison_engine.settings import VALIDATION_OUTPUT_DIR

from .coverage_summary_builder import build_coverage_summary
from .model_validation_compare_builder import build_model_validation_compare
from .promotion_support_builder import build_promotion_decision_support
from .validation_summary_builder import build_validation_summary


def build_validation_assimilation_artifacts_from_files(
    *,
    scope_type: str,
    scope_id: str,
    validation_report_path: Path | None = None,
    validation_freshness_path: Path | None = None,
    label_coverage_path: Path | None = None,
    feature_store_summary_path: Path | None = None,
    output_dir: Path | None = None,
    policy_refs: dict[str, Any] | None = None,
    upstream_refs: dict[str, Any] | None = None,
) -> dict:
    validation_report = _load_json(validation_report_path)
    validation_freshness = _load_json(validation_freshness_path)
    label_coverage = _load_json(label_coverage_path)
    feature_store_summary = _load_json(feature_store_summary_path)
    validation_summary = build_validation_summary(
        scope_type=scope_type,
        scope_id=scope_id,
        validation_report=validation_report,
        validation_freshness=validation_freshness,
        coverage_summary=label_coverage,
        label_coverage_report=label_coverage,
        feature_store_summary=feature_store_summary,
        policy_refs=policy_refs,
        upstream_refs=upstream_refs,
    )
    coverage_summary = build_coverage_summary(
        scope_type=scope_type,
        scope_id=scope_id,
        validation_report=validation_report,
        label_coverage_report=label_coverage,
        feature_store_summary=feature_store_summary,
        policy_refs=policy_refs,
        upstream_refs=upstream_refs,
    )
    promotion_support = build_promotion_decision_support(
        scope_type=scope_type,
        scope_id=scope_id,
        validation_summary=validation_summary,
        validation_freshness=validation_freshness,
        coverage_summary=coverage_summary,
        policy_refs=policy_refs,
    )
    model_compare = build_model_validation_compare(
        scope_type=scope_type,
        scope_id=scope_id,
        validation_report=validation_report,
        coverage_summary=coverage_summary,
        policy_refs=policy_refs,
    )
    artifacts = {
        "validation_summary": validation_summary,
        "coverage_summary": coverage_summary,
        "promotion_support": promotion_support,
        "model_validation_compare": model_compare,
    }
    if output_dir is not None:
        write_validation_assimilation_artifacts(
            output_dir=output_dir,
            scope_id=scope_id,
            artifacts=artifacts,
        )
    return artifacts


def write_validation_assimilation_artifacts(
    *,
    output_dir: Path | None,
    scope_id: str,
    artifacts: dict[str, dict],
) -> dict[str, Path]:
    out_dir = output_dir or VALIDATION_OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    safe_scope_id = _slugify(scope_id)
    paths = {
        "validation_summary": out_dir / f"validation_summary_{safe_scope_id}.json",
        "coverage_summary": out_dir / f"coverage_summary_{safe_scope_id}.json",
        "promotion_support": out_dir / f"promotion_support_{safe_scope_id}.json",
        "model_validation_compare": out_dir / f"model_validation_compare_{safe_scope_id}.json",
    }
    for key, path in paths.items():
        payload = artifacts.get(key) or {}
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return paths


def _load_json(path: Path | None) -> dict:
    if path is None or not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _slugify(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in str(value or "all").strip()) or "all"
