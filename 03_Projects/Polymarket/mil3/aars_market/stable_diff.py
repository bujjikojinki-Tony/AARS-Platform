from __future__ import annotations

from typing import Any, Mapping


SUMMARY_FIELDS = (
    "total_return",
    "max_drawdown",
    "fees",
    "funding",
    "final_net_exposure",
    "max_effective_leverage",
    "min_margin_buffer_pct",
    "max_liquidation_risk",
    "liquidation_events",
)


def _semantic_projection(payload: Mapping[str, Any]) -> dict[str, Any]:
    strategies = {
        item["id"]: {key: item["summary"].get(key) for key in SUMMARY_FIELDS}
        for item in payload.get("strategies", [])
    }
    funding = payload.get("funding", {})
    return {
        "market": {
            "symbol": payload.get("market", {}).get("symbol"),
            "timeframe": payload.get("market", {}).get("timeframe"),
            "latest_candle_at": payload.get("market", {}).get("latest_candle_at"),
            "freshness_status": payload.get("market", {}).get("freshness_status"),
            "degraded": payload.get("market", {}).get("degraded"),
        },
        "selection": {
            "replay_window": payload.get("selection", {}).get("replay_window"),
        },
        "funding": {"coverage": funding.get("coverage")},
        "highest_risk": payload.get("highest_risk"),
        "latest_stable_view": payload.get("latest_stable_view"),
        "strategies": strategies,
        "review_gate": {
            "disposition": payload.get("review_gate", {}).get("disposition"),
            "reasons": payload.get("review_gate", {}).get("reasons"),
            "live_execution_allowed": payload.get("review_gate", {}).get("live_execution_allowed"),
        },
    }


def _flatten(value: Any, prefix: str = "") -> dict[str, Any]:
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key in sorted(value):
            path = f"{prefix}.{key}" if prefix else str(key)
            result.update(_flatten(value[key], path))
        return result
    if isinstance(value, (list, tuple)):
        return {prefix: list(value)}
    return {prefix: value}


def _severity(path: str, before: Any, after: Any) -> str:
    if path.endswith("live_execution_allowed") and after is not False:
        return "CRITICAL"
    if "liquidation_events" in path and before != after:
        return "HIGH"
    if path.endswith("disposition") or path.endswith("state") or "coverage.status" in path:
        return "ELEVATED"
    if "liquidation_risk" in path or "margin_buffer" in path:
        return "ELEVATED"
    return "INFO"


def compare_stable_views(
    before: Mapping[str, Any],
    after: Mapping[str, Any],
    *,
    before_id: str | None = None,
    after_id: str | None = None,
) -> dict[str, Any]:
    left = _flatten(_semantic_projection(before))
    right = _flatten(_semantic_projection(after))
    changes: list[dict[str, Any]] = []
    for path in sorted(set(left) | set(right)):
        old = left.get(path)
        new = right.get(path)
        if old == new:
            continue
        delta = new - old if isinstance(old, (int, float)) and isinstance(new, (int, float)) else None
        changes.append(
            {
                "path": path,
                "before": old,
                "after": new,
                "delta": delta,
                "severity": _severity(path, old, new),
            }
        )
    material = sum(change["severity"] != "INFO" for change in changes)
    return {
        "schema_version": "mil3.stable-view-diff.v1",
        "execution_mode": "PAPER_ONLY",
        "before_view_id": before_id,
        "after_view_id": after_id,
        "summary": {
            "changed_fields": len(changes),
            "material_changes": material,
            "status": "UNCHANGED" if not changes else "MATERIAL_CHANGE" if material else "CHANGED",
        },
        "changes": changes,
    }
