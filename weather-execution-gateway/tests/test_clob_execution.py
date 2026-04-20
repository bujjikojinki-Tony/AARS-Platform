from weather_execution_gateway.models.order_intent import OrderIntent
from weather_execution_gateway.polymarket.clob_execution import (
    DisabledClobExecutionAdapter,
    build_clob_order_request,
    is_clob_adapter_ready,
)


def test_build_clob_order_request_from_intent():
    intent = OrderIntent(
        schema_version="execution_intent.v1",
        intent_id="intent_1",
        market_id="market_1",
        signal_id="signal_1",
        decision_ref="decision_intent_1",
        authorization_ref="approval_intent_1",
        side="buy",
        price=0.42,
        size=10,
        post_only=True,
        max_slippage_pct=0.02,
        approved=True,
    )

    request = build_clob_order_request(intent, token_id="token_1")

    assert request.intent_id == "intent_1"
    assert request.market_id == "market_1"
    assert request.token_id == "token_1"
    assert request.side == "buy"
    assert request.price == 0.42
    assert request.approved is True


def test_disabled_clob_adapter_rejects_orders():
    intent = OrderIntent(
        schema_version="execution_intent.v1",
        intent_id="intent_1",
        market_id="market_1",
        signal_id="signal_1",
        decision_ref="decision_intent_1",
        authorization_ref="approval_intent_1",
        side="buy",
        price=0.42,
        size=10,
        approved=True,
    )
    request = build_clob_order_request(intent, token_id="token_1")

    result = DisabledClobExecutionAdapter().submit_order(request)

    assert result.accepted is False
    assert result.status == "rejected"
    assert result.reason == "clob_adapter_disabled"
    assert result.external_order_id is None


def test_clob_adapter_ready_requires_all_live_switches():
    assert (
        is_clob_adapter_ready(
            {
                "adapter": {
                    "enabled": True,
                    "mode": "live",
                    "allow_real_orders": True,
                    "signed_client_configured": True,
                }
            }
        )
        is True
    )
    assert (
        is_clob_adapter_ready(
            {
                "adapter": {
                    "enabled": True,
                    "mode": "live",
                    "allow_real_orders": True,
                    "signed_client_configured": False,
                }
            }
        )
        is False
    )
