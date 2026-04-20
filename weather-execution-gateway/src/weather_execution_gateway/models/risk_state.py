from pydantic import BaseModel


class RiskState(BaseModel):
    market_allowed: bool
    approval_present: bool
    kill_switch_active: bool
    notional_allowed: bool
    execution_enabled: bool

    market_notional: float = 0.0
    total_notional: float = 0.0
    new_order_notional: float = 0.0

    reason: str | None = None
