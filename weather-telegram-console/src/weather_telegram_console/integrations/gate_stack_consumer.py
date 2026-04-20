from __future__ import annotations

from dataclasses import dataclass

GATE_STACK_API_SCHEMA_VERSION = "gate_stack_api.v1"
GATE_STACK_GATE_SOURCE_VALUES = {"api", "unified_fallback", "local_fallback"}


@dataclass(frozen=True)
class GateStackConsumerResult:
    payload: dict
    raw_payload: dict
    gate_source: str
    schema_version_checked: str
    generated_at: str | None
    market_view: dict | None


def consume_gate_stack_payload(payload: dict | None, *, market_id: str | None = None) -> GateStackConsumerResult:
    gate_stack_api = payload if isinstance(payload, dict) else {}
    schema_version = str(gate_stack_api.get("schema_version") or "")
    selected_market_id = str(market_id or gate_stack_api.get("market_id") or "").strip()

    market_view = _find_market_view(gate_stack_api, market_id=selected_market_id)
    source_payload = market_view if isinstance(market_view, dict) else gate_stack_api

    contracts = gate_stack_api.get("contracts")
    if not isinstance(contracts, dict):
        contracts = {}

    gate_source = str(
        source_payload.get("gate_source")
        or gate_stack_api.get("gate_source")
        or contracts.get("gate_source")
        or "api"
    ).strip().lower()
    if gate_source not in GATE_STACK_GATE_SOURCE_VALUES:
        gate_source = "api"

    return GateStackConsumerResult(
        payload=source_payload if isinstance(source_payload, dict) else gate_stack_api,
        raw_payload=gate_stack_api,
        gate_source=gate_source,
        schema_version_checked=schema_version or "unknown",
        generated_at=str(gate_stack_api.get("generated_at") or "").strip() or None,
        market_view=market_view if isinstance(market_view, dict) else None,
    )


def _find_market_view(payload: dict, *, market_id: str) -> dict | None:
    if not market_id:
        return None
    views = payload.get("market_gate_views")
    if not isinstance(views, list):
        return None
    for view in views:
        if not isinstance(view, dict):
            continue
        if str(view.get("market_id") or "").strip() == market_id:
            return view
    return None
