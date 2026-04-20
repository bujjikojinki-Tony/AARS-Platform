from weather_execution_gateway.models.order_intent import OrderIntent


class PolymarketOrderGateway:
    def submit_dry_run(self, intent: OrderIntent) -> dict:
        return {
            "intent_id": intent.intent_id,
            "market_id": intent.market_id,
            "side": intent.side,
            "price": intent.price,
            "size": intent.size,
            "status": "dry_run_only",
        }
