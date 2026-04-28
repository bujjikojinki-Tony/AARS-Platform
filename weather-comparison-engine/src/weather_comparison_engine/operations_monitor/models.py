from __future__ import annotations

from typing import Any, NotRequired, TypedDict


class FocusMarketItem(TypedDict, total=False):
    market_id: str
    market_family: str
    city: str
    market_question_short: str
    focus_reason: str
    latest_priority_score: float
    next_action: str
    primary_state: str
    secondary_states: list[str]
    display_priority: float
    is_selected_market: bool
    pinned_by_user: bool


class MarketMonitorCard(TypedDict, total=False):
    schema_version: str
    market_id: str
    city: str
    market_family: str
    market_question_short: str
    opportunity_score: float
    difficulty_label: str
    best_model: str
    freshness_status: str
    source_precision_score: float
    latest_alert_severity: str
    latest_anomaly_score: float | None
    primary_state: str
    secondary_states: list[str]
    primary_state_reason: str
    display_priority: float
    can_execute: bool
    primary_block_reason: str
    recommended_action: str
    is_focus_market: bool
    scan_priority: str
    upstream_refs: dict[str, Any]


class OperationsMonitorView(TypedDict, total=False):
    schema_version: str
    generated_at: str
    page_context: dict[str, Any]
    global_summary: dict[str, Any]
    focus_markets: list[FocusMarketItem]
    market_monitor_cards: list[MarketMonitorCard]
    system_health: dict[str, Any]
    ops_alerts: list[dict[str, Any]]
    selected_market_quick_detail: dict[str, Any]
    view_context: dict[str, Any]
    upstream_refs: dict[str, Any]
