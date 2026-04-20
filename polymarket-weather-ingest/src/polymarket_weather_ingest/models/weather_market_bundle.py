from pydantic import BaseModel

from polymarket_weather_ingest.models.market_content import MarketContent
from polymarket_weather_ingest.models.market_price_state import MarketPriceState


class WeatherMarketBundle(BaseModel):
    market: MarketContent
    price_state: MarketPriceState
