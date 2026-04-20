class PolymarketMarketReader:
    def get_market_stub(self, market_id: str) -> dict:
        return {
            "market_id": market_id,
            "status": "stub",
        }
