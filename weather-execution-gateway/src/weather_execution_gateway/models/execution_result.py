from pydantic import BaseModel


class ExecutionResult(BaseModel):
    intent_id: str
    status: str
    mode: str

    accepted: bool
    reason: str | None = None

    simulated_order_id: str | None = None
