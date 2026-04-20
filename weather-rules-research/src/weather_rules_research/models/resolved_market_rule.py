from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ResolvedMarketRule(BaseModel):
    """Phase-2 resolver output for one live Polymarket market."""

    model_config = ConfigDict(extra="allow")

    schema_version: str = Field(default="resolved_market_rule.v2")
    resolver_contract_version: str = Field(default="resolver_contract.v1")
    market_id: str
    market_question: str | None = None

    resolver_status: str
    resolver_reason: str
    resolver_name: str
    resolver_confidence: float = 0.0

    market_family: str
    resolution_scope: str
    supported_by_current_pipeline: bool
    required_data_source: str | None = None
    required_sources: list[str] = Field(default_factory=list)
    band_scheme: str | None = None
    settlement_source_type: str | None = None
    official_vs_proxy_source: str | None = None
    source_match_grade: str | None = None
    official_source_url: str | None = None
    source_note: str | None = None

    location_name: str | None = None
    station_name: str | None = None
    station_id: str | None = None
    nws_station_id: str | None = None
    cdo_station_id: str | None = None
    target_date: str | None = None
    variable_name: str | None = None
    timezone: str | None = None
    unit: str | None = None

    source_rule_market_id: str | None = None
    failure_reason: str | None = None
