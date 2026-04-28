from __future__ import annotations

from pydantic import BaseModel


class OpportunityBoardRow(BaseModel):
    row_id: str
    city: str
    country: str = "-"
    market_family: str
    active_market_count: int
    opportunity_score: float
    opportunity_rank: int
    difficulty_score: float
    difficulty_label: str
    best_model: str
    best_source_stack: list[str]
    source_precision_score: float
    freshness_status: str
    alert_count: int
    latest_alert_severity: str
    anomaly_count: int
    latest_anomaly_score: float | None = None
    gate_risk_summary: str
    recommended_action: str
    opportunity_reason: str
    difficulty_reason: str
    best_model_reason: str
    upstream_refs: dict
