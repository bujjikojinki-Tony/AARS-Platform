from pydantic import BaseModel
from pydantic import Field

EXECUTION_INTENT_SCHEMA_VERSION = "execution_intent.v1"


class OrderIntent(BaseModel):
    schema_version: str = EXECUTION_INTENT_SCHEMA_VERSION
    intent_id: str
    market_id: str
    signal_id: str | None = None
    decision_ref: str | None = None
    authorization_ref: str | None = None

    side: str
    price: float
    size: float

    post_only: bool = True
    max_slippage_pct: float = 0.02
    approved: bool = False
    probability_mode: str | None = None
    execution_constraint: str | None = None
    calibration_status: str | None = None
    contract_version: str | None = None
    probability_contract: dict = Field(default_factory=dict)
