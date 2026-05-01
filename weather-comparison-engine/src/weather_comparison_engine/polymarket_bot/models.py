from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass


@dataclass(slots=True)
class MarketSnapshot:
    market_id: str
    question: str
    yes_price: float
    no_price: float
    liquidity: float
    spread: float
    fetched_at: str
    source: str = "mock"
    slug: str | None = None
    category: str | None = None

    def to_record(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class StrategySignal:
    signal_id: str
    market_id: str
    strategy_id: str
    side: str
    model_probability: float
    market_probability: float
    edge_percent: float
    confidence: str
    reason: str
    created_at: str
    z_score: float | None = None

    def to_record(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class OpportunityCandidate:
    candidate_id: str
    signal_id: str
    market_id: str
    question: str
    side: str
    market_probability: float
    model_probability: float
    edge_percent: float
    liquidity: float
    spread: float
    confidence_tier: str
    risk_status: str
    action_status: str
    created_at: str
    z_score: float | None = None
    expires_at: str | None = None

    def to_record(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class RiskGateResult:
    candidate_id: str
    status: str
    checks: dict[str, bool]
    reasons: list[str]
    checked_at: str

    def to_record(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class ExecutionDecision:
    decision_id: str
    candidate_id: str
    mode: str
    action: str
    approval_required: bool
    approval_status: str
    position_size: float
    expected_cost: float
    risk_status: str
    execution_status: str
    created_at: str
    requested_by: str | None = None
    approved_by: str | None = None
    executed_at: str | None = None

    def to_record(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class SimulationResult:
    simulation_id: str
    decision_id: str
    candidate_id: str
    side: str
    entry_price: float
    position_size: float
    simulated_cost: float
    expected_probability: float
    expected_value: float
    max_loss: float
    max_gain: float
    result_status: str
    created_at: str

    def to_record(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class AuditLog:
    event_id: str
    event_type: str
    object_type: str
    object_id: str
    created_at: str
    payload_json: str | None = None

    def to_record(self) -> dict:
        return asdict(self)
