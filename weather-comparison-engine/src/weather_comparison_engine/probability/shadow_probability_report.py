from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from weather_comparison_engine.schemas.probability_state import ProbabilityState


def write_probability_state(state: ProbabilityState, output_dir: str | Path) -> Path:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"probability_state_{state.market_id}.json"
    out.write_text(
        json.dumps(state.model_dump(mode="json", exclude_none=True), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return out


def build_probability_shadow_report(
    states: list[ProbabilityState],
    state_paths: list[Path],
    *,
    contract: dict | None = None,
) -> dict:
    contract = contract or {}
    active = [state for state in states if state.model_probability is not None]
    blocked = [state for state in states if state.model_probability is None]
    reason_counts = Counter(state.probability_reason or "unknown" for state in blocked)
    family_counts = Counter(state.market_family or "unknown" for state in states)

    ranked_edges = sorted(
        [
            {
                "market_id": state.market_id,
                "market_family": state.market_family,
                "market_implied_probability": state.market_implied_probability,
                "fair_value": state.fair_value,
                "edge": state.edge,
                "confidence_adjusted_edge": state.confidence_adjusted_edge,
                "probability_reason": state.probability_reason,
            }
            for state in active
            if state.edge is not None
        ],
        key=lambda row: abs(float(row["confidence_adjusted_edge"] or row["edge"] or 0.0)),
        reverse=True,
    )

    return {
        "schema_version": "probability_shadow_report.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "shadow",
        "calibration_status": contract.get("calibration_status", "not_calibrated"),
        "probability_mode": contract.get("probability_mode", "heuristic_not_calibrated"),
        "execution_constraint": contract.get("execution_constraint", "manual_advisory_only"),
        "approved_for_live": bool(contract.get("approved_for_live", False)),
        "deployment_mode": contract.get("deployment_mode", "shadow"),
        "promotion_reason": contract.get("promotion_reason"),
        "contract_source": contract.get("contract_source"),
        "validation_report_generated_at": contract.get("validation_report_generated_at"),
        "method": "band_support_heuristic",
        "decision_note": (
            "Shadow probability is a heuristic decision aid, not a calibrated probability "
            "and not an execution signal by itself."
        ),
        "tracked_markets": len(states),
        "active_states": len(active),
        "blocked_states": len(blocked),
        "blocked_reason_counts": dict(reason_counts),
        "market_family_counts": dict(family_counts),
        "top_edges": ranked_edges[:10],
        "state_paths": [str(path) for path in state_paths],
        "states": [state.model_dump(mode="json", exclude_none=True) for state in states],
    }


def write_probability_shadow_report(report: dict, path: str | Path) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return out
