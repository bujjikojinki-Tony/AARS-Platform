from polymarket_weather_ingest.ingest.gamma_client import GammaClient


class MarketSearch:
    def __init__(self, client: GammaClient) -> None:
        self.client = client

    def search(self, query: str) -> dict:
        return self.client.search_sync(query=query)
