from backend.models.core import MarketSnapshot
from backend.models.weather import WeatherMarketDescriptor
from backend.normalization.market_question_parser import parse_market_question


class MarketQuestionParser:
    def __init__(self, default_year: int = 2026):
        self.default_year = default_year

    def parse(self, market_id: str, question: str) -> WeatherMarketDescriptor:
        market = MarketSnapshot(
            market_id=market_id,
            question=question,
            yes_price=0.5,
            no_price=0.5,
            liquidity=0,
            spread=0,
        )
        return parse_market_question(market, default_year=self.default_year)
