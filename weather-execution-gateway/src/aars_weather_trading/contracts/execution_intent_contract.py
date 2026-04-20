from dataclasses import dataclass

from aars_weather_trading.contracts.contract_versions import EXECUTION_INTENT_CONTRACT_VERSION


@dataclass(frozen=True)
class ExecutionIntentContract:
    intent_id: str
    market_id: str
    side: str
    order_type: str
    limit_price: float | None
    size: float
    mode: str
    decision_ref: str
    authorization_ref: str
    probability_mode: str
    execution_constraint: str
    contract_version: str = EXECUTION_INTENT_CONTRACT_VERSION

