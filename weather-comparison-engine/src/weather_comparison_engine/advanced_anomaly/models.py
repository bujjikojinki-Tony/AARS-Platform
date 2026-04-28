from __future__ import annotations

from pydantic import BaseModel, Field


class MarketAnomalyEventV2(BaseModel):
    schema_version: str = "market_anomaly_event.v2"
    event_id: str
    generated_at: str
    market_id: str
    market_family: str
    anomaly_score: float
    price_velocity_score: float | None = None
    edge_dislocation_score: float | None = None
    evidence_mismatch_score: float | None = None
    microstructure_stress_score: float | None = None
    peer_relative_anomaly_score: float | None = None
    intervention_like_score: float | None = None
    intervention_like_flag: bool | None = None
    signals: list[str] = Field(default_factory=list)
    primary_reason: str | None = None
    recommended_operator_action: str | None = None
    policy_refs: dict = Field(default_factory=dict)
    upstream_refs: dict = Field(default_factory=dict)


class FamilyAnomalySummaryV1(BaseModel):
    schema_version: str = "family_anomaly_summary.v1"
    generated_at: str
    market_family: str
    scanned_market_count: int
    high_anomaly_count: int = 0
    high_intervention_like_count: int = 0
    top_anomalies: list[dict] = Field(default_factory=list)
    family_risk_summary: str | None = None
    policy_refs: dict = Field(default_factory=dict)
