from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class MarketUniverseMarket:
    schema_version: str
    market_id: str
    question: str
    city: str
    country: str
    market_family: str
    target_date: str
    band_scheme: str
    active_status: str
    liquidity_score: float
    spread: float
    scan_priority: str
    seeded_from_opportunity_seed: bool
    upstream_refs: dict


@dataclass(slots=True)
class MarketUniverseSnapshot:
    schema_version: str
    generated_at: str
    markets: list[dict]
    source_refs: dict


@dataclass(slots=True)
class EvidenceScanRow:
    schema_version: str
    market_id: str
    market_family: str
    city: str
    forecast_snapshot_ref: str
    observation_snapshot_ref: str
    comparison_point_ref: str
    source_precision_score: float
    freshness_status: str
    best_model: str
    best_source_stack: list[str]
    scan_status: str
    generated_at: str
    upstream_refs: dict


@dataclass(slots=True)
class ScannerStatus:
    schema_version: str
    generated_at: str
    total_markets: int
    scanned_markets: int
    stale_markets: int
    unavailable_markets: int
    alert_markets: int
    backlog_count: int
    next_scan_eta: str
    summary: dict
