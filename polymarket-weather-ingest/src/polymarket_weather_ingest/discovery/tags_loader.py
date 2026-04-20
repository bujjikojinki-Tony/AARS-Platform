from polymarket_weather_ingest.ingest.gamma_client import GammaClient


class TagsLoader:
    def __init__(self, client: GammaClient) -> None:
        self.client = client

    def load(self) -> list[dict]:
        return self.client.fetch_tags_sync()
