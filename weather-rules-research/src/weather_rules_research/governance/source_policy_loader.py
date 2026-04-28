from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from weather_rules_research.settings import SOURCE_POLICY_REGISTRY_JSON

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
