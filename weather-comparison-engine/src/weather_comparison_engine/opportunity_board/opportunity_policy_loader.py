from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from weather_comparison_engine.settings import (
    ACTION_MAPPING_POLICY_JSON,
    BUY_SELL_DECISION_POLICY_JSON,
    DIFFICULTY_SCORING_POLICY_JSON,
    FRESHNESS_MAPPING_POLICY_JSON,
    MODEL_RECOMMENDATION_POLICY_JSON,
    OPPORTUNITY_SCORING_POLICY_JSON,
    SOURCE_PRECISION_POLICY_JSON,
)


POLICY_PATHS = {
    "opportunity_scoring_policy": OPPORTUNITY_SCORING_POLICY_JSON,
    "difficulty_scoring_policy": DIFFICULTY_SCORING_POLICY_JSON,
    "model_recommendation_policy": MODEL_RECOMMENDATION_POLICY_JSON,
    "action_mapping_policy": ACTION_MAPPING_POLICY_JSON,
    "freshness_mapping_policy": FRESHNESS_MAPPING_POLICY_JSON,
    "source_precision_policy": SOURCE_PRECISION_POLICY_JSON,
    "buy_sell_decision_policy": BUY_SELL_DECISION_POLICY_JSON,
}


def load_opportunity_policy_bundle(policy_paths: dict[str, Path] | None = None) -> dict[str, dict]:
    paths = policy_paths or POLICY_PATHS
    bundle: dict[str, dict] = {}
    for key, path in paths.items():
        payload = _load_json(path)
        if isinstance(payload, dict):
            bundle[key] = payload
    return bundle


def policy_ref(policy: dict | None, fallback: str) -> str:
    if not isinstance(policy, dict):
        return fallback
    return str(policy.get("policy_id") or fallback)


def _load_json(path: Path) -> Any:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
