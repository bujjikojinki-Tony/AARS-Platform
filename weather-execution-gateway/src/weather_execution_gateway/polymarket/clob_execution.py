from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, Field

from weather_execution_gateway.models.order_intent import OrderIntent


class ClobOrderRequest(BaseModel):
    intent_id: str
    market_id: str
    token_id: str | None = None
    side: str
    price: float
    size: float
    post_only: bool = True
    max_slippage_pct: float = 0.02
    approved: bool = False


class ClobOrderResult(BaseModel):
    intent_id: str
    market_id: str
    status: str
    accepted: bool
    reason: str | None = None
    mode: str = "disabled"
    external_order_id: str | None = None
    raw_response: dict = Field(default_factory=dict)


class ClobExecutionAdapter(Protocol):
    def submit_order(self, request: ClobOrderRequest) -> ClobOrderResult:
        """Submit or reject a CLOB order request."""


class DisabledClobExecutionAdapter:
    """
    Safe production-facing adapter stub.

    It implements the future live adapter contract, but always rejects order submission.
    This keeps live execution plumbing testable without introducing private-key handling
    or accidental real orders.
    """

    mode = "disabled"

    def submit_order(self, request: ClobOrderRequest) -> ClobOrderResult:
        return ClobOrderResult(
            intent_id=request.intent_id,
            market_id=request.market_id,
            status="rejected",
            accepted=False,
            reason="clob_adapter_disabled",
            mode=self.mode,
            external_order_id=None,
            raw_response={
                "message": "Real Polymarket CLOB execution adapter is disabled.",
                "token_id_present": request.token_id is not None,
            },
        )


def build_clob_order_request(
    intent: OrderIntent,
    *,
    token_id: str | None = None,
) -> ClobOrderRequest:
    return ClobOrderRequest(
        intent_id=intent.intent_id,
        market_id=intent.market_id,
        token_id=token_id,
        side=intent.side,
        price=intent.price,
        size=intent.size,
        post_only=intent.post_only,
        max_slippage_pct=intent.max_slippage_pct,
        approved=intent.approved,
    )


def is_clob_adapter_ready(config: dict) -> bool:
    adapter = config.get("adapter") or {}
    return (
        bool(adapter.get("enabled", False))
        and adapter.get("mode") == "live"
        and bool(adapter.get("allow_real_orders", False))
        and bool(adapter.get("signed_client_configured", False))
    )
