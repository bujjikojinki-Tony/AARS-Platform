from __future__ import annotations

import json
from pathlib import Path

from weather_rules_research.models.market_rule import MarketRule
from weather_rules_research.rules.market_resolution_registry import (
    MarketResolution,
    MarketResolverRegistry,
)
from weather_rules_research.rules.market_taxonomy import MarketTaxonomy


def load_rulebook(path: str | Path) -> list[MarketRule]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))

    if isinstance(payload, dict):
        rules_payload = payload.get("rules", [])
    elif isinstance(payload, list):
        rules_payload = payload
    else:
        rules_payload = []

    return [MarketRule.model_validate(rule) for rule in rules_payload]


def resolve_rule_for_market(
    market_snapshot: dict,
    rules: list[MarketRule],
) -> tuple[MarketRule | None, str, MarketTaxonomy]:
    resolution: MarketResolution = resolve_market_resolution(market_snapshot, rules)
    return resolution.rule, resolution.reason, resolution.taxonomy


def resolve_market_resolution(
    market_snapshot: dict,
    rules: list[MarketRule],
) -> MarketResolution:
    return MarketResolverRegistry().resolve(market_snapshot, rules)
