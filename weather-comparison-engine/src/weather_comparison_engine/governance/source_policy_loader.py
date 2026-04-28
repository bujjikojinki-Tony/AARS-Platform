from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any
import re

from weather_comparison_engine.settings import SOURCE_POLICY_REGISTRY_JSON

SOURCE_POLICY_REGISTRY_SCHEMA_VERSION = "source_policy_registry.v1"


def _default_registry() -> dict[str, Any]:
    return {"schema_version": SOURCE_POLICY_REGISTRY_SCHEMA_VERSION, "sources": []}


@lru_cache(maxsize=8)
def load_source_policy_registry(path: str | Path | None = None) -> dict[str, Any]:
    registry_path = Path(path or SOURCE_POLICY_REGISTRY_JSON)
    if not registry_path.exists():
        return _default_registry()
    try:
        payload = json.loads(registry_path.read_text(encoding="utf-8"))
    except Exception:
        return _default_registry()
    if not isinstance(payload, dict):
        return _default_registry()
    payload.setdefault("schema_version", SOURCE_POLICY_REGISTRY_SCHEMA_VERSION)
    if not isinstance(payload.get("sources"), list):
        payload["sources"] = []
    return payload


def get_source_policy_definition(source_name: str, *, path: str | Path | None = None) -> dict[str, Any]:
    registry = load_source_policy_registry(path)
    for source in registry.get("sources") or []:
        if isinstance(source, dict) and str(source.get("source_name") or "") == str(source_name):
            return source
    return {}


def get_source_policy_threshold_seconds(
    source_name: str,
    *,
    threshold_key: str = "stale_threshold",
    path: str | Path | None = None,
) -> int | None:
    definition = get_source_policy_definition(source_name, path=path)
    if not definition:
        return None
    return _parse_duration_seconds(definition.get(threshold_key))


def get_source_policy_freshness_thresholds(
    source_name: str,
    *,
    path: str | Path | None = None,
) -> dict[str, int | None]:
    definition = get_source_policy_definition(source_name, path=path)
    if not definition:
        return {"fresh_threshold_seconds": None, "stale_threshold_seconds": None}
    return {
        "fresh_threshold_seconds": _parse_duration_seconds(definition.get("fresh_threshold")),
        "stale_threshold_seconds": _parse_duration_seconds(definition.get("stale_threshold")),
    }


def _parse_duration_seconds(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value).strip().lower()
    if not text:
        return None
    if text.isdigit():
        return int(text)
    match = re.fullmatch(r"(?P<value>\d+(?:\.\d+)?)(?P<unit>s|m|h|d)", text)
    if not match:
        return None
    amount = float(match.group("value"))
    unit = match.group("unit")
    multiplier = {"s": 1, "m": 60, "h": 3600, "d": 86400}[unit]
    return int(amount * multiplier)
