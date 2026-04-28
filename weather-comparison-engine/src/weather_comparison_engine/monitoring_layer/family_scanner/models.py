from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class FamilyScanInput:
    market_rows: list[dict]
    comparison_history: list[dict]
    probability_states: dict[str, dict]


@dataclass(slots=True)
class MarketAnomalyEvent:
    schema_version: str
    event_id: str
    market_id: str
    market_family: str
    anomaly_score: float
    intervention_like_score: float
    signals: list[str]
    primary_reason: str
    recommended_operator_action: str
    generated_at: str
    indicator_version: str = "v1"
    threshold_policy_version: str = "v1"
