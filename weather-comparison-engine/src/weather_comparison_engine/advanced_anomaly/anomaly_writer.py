from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from weather_comparison_engine.settings import ADVANCED_ANOMALY_OUTPUT_DIR

from .anomaly_v2_builder import build_advanced_anomaly_outputs


def write_advanced_anomaly_artifacts(
    *,
    output_dir: Path | None = None,
    market_rows: list[dict[str, Any]],
    comparison_history: list[dict[str, Any]],
    probability_states: dict[str, dict[str, Any]] | None = None,
    source_policy_status: dict[str, Any] | None = None,
    policy_refs: dict[str, Any] | None = None,
) -> dict[str, Path]:
    out_dir = output_dir or ADVANCED_ANOMALY_OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = build_advanced_anomaly_outputs(
        market_rows=market_rows,
        comparison_history=comparison_history,
        probability_states=probability_states,
        source_policy_status=source_policy_status,
        policy_refs=policy_refs,
    )

    paths: dict[str, Path] = {}
    for event in outputs.get("market_events") or []:
        market_id = str(event.get("market_id") or "unknown")
        safe_market_id = _slugify(market_id)
        path = out_dir / f"market_anomaly_{safe_market_id}_v2.json"
        path.write_text(json.dumps(event, indent=2, ensure_ascii=False), encoding="utf-8")
        paths[f"market:{market_id}"] = path

    for family_summary in outputs.get("family_summaries") or []:
        family = str(family_summary.get("market_family") or "unknown")
        safe_family = _slugify(family)
        path = out_dir / f"family_anomaly_summary_{safe_family}.json"
        path.write_text(json.dumps(family_summary, indent=2, ensure_ascii=False), encoding="utf-8")
        paths[f"family:{family}"] = path

    return paths


def _slugify(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in str(value or "unknown").strip()) or "unknown"
