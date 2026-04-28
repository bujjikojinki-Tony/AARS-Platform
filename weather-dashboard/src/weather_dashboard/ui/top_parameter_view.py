from __future__ import annotations

from typing import TypedDict


TOP_PARAMETER_VIEW_VERSION = "top_parameter_view.v2"


class TopParameterCardRow(TypedDict):
    label: str
    value: object


class TopParameterCard(TypedDict):
    title: str
    metric_label: str
    metric_value: object
    rows: list[tuple[str, object]]


class TopParameterView(TypedDict):
    schema_version: str
    market_id: str
    market_family: str
    market_question: str
    location_name: str
    target_date: str
    variable_name: str
    polymarket: dict[str, object]
    weather: dict[str, object]
    forecast: dict[str, object]
    source_contract: dict[str, object]
    decision: dict[str, object]
    canonical_unit: str
    source_priority: str
    fallback_mode: str
    policy_refs: dict[str, object]
    normalization: dict[str, object]
    cards: list[TopParameterCard]
