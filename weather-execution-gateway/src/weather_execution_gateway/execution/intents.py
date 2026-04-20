from weather_execution_gateway.models.order_intent import OrderIntent


def build_order_intent(
    intent_id: str,
    market_id: str,
    side: str,
    price: float,
    size: float,
    approved: bool,
    signal_id: str | None = None,
    decision_ref: str | None = None,
    authorization_ref: str | None = None,
) -> OrderIntent:
    return OrderIntent(
        schema_version="execution_intent.v1",
        intent_id=intent_id,
        market_id=market_id,
        signal_id=signal_id,
        decision_ref=decision_ref,
        authorization_ref=authorization_ref,
        side=side,
        price=price,
        size=size,
        approved=approved,
    )
