from __future__ import annotations

from datetime import datetime
from datetime import timezone
from typing import Any

from pydantic import BaseModel
from pydantic import Field

from .enums import ActionStatus
from .enums import ExecutionMode
from .enums import ExecutionStatus
from .enums import RiskStatus
from .enums import Side


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class MarketSnapshot(BaseModel):
    market_id: str
    question: str
    yes_price: float
    no_price: float
    liquidity: float
    spread: float
    source: str = "mock"
    fetched_at: str = Field(default_factory=now_iso)


class WeatherMarketDescriptor(BaseModel):
    market_id: str
    question: str
    city: str
    target_date: str
    threshold: float
    direction: str
    measurement: str | None = None
    comparator_text: str | None = None


class StrategySignal(BaseModel):
    signal_id: str
    market_id: str
    strategy_id: str
    side: Side
    model_probability: float
    market_probability: float
    edge_percent: float
    z_score: float | None = None
    confidence: str = "LOW"
    reason: str
    created_at: str = Field(default_factory=now_iso)


class OpportunityCandidate(BaseModel):
    candidate_id: str
    signal_id: str
    market_id: str
    question: str
    side: Side
    market_probability: float
    model_probability: float
    edge_percent: float
    z_score: float | None = None
    liquidity: float
    spread: float
    confidence_tier: str = "LOW"
    risk_status: RiskStatus = RiskStatus.WARN
    action_status: ActionStatus = ActionStatus.WATCH
    created_at: str = Field(default_factory=now_iso)


class RiskGateResult(BaseModel):
    candidate_id: str
    status: RiskStatus
    checks: dict[str, bool]
    reasons: list[str]
    checked_at: str = Field(default_factory=now_iso)


class ExecutionDecision(BaseModel):
    decision_id: str
    candidate_id: str
    mode: ExecutionMode = ExecutionMode.SIMULATION
    action: str
    position_size: float
    expected_cost: float
    risk_status: RiskStatus
    execution_status: ExecutionStatus = ExecutionStatus.QUEUED
    created_at: str = Field(default_factory=now_iso)
    executed_at: str | None = None


class SimulationResult(BaseModel):
    simulation_id: str
    decision_id: str
    candidate_id: str
    side: Side
    entry_price: float
    position_size: float
    simulated_cost: float
    expected_probability: float
    expected_value: float
    max_loss: float
    max_gain: float
    result_status: str = "COMPLETED"
    created_at: str = Field(default_factory=now_iso)


class AuditLogEvent(BaseModel):
    event_id: str
    event_type: str
    object_type: str
    object_id: str
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=now_iso)
