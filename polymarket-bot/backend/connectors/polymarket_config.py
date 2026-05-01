from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from backend.models.polymarket import PolymarketConnectorMode


class PolymarketConnectorConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    mode: PolymarketConnectorMode = PolymarketConnectorMode.MOCK_ONLY
    market_source_mode: PolymarketConnectorMode | None = None
    allow_polymarket_network: bool = False
    gamma_base_url: str = "https://gamma-api.polymarket.com"
    clob_base_url: str = "https://clob.polymarket.com"
    request_timeout_seconds: float = 8.0
    max_markets: int = 50
    weather_keywords: list[str] = Field(
        default_factory=lambda: [
            "weather",
            "temperature",
            "temp",
            "high temperature",
            "low temperature",
            "rain",
            "rainfall",
            "precipitation",
            "snow",
            "hurricane",
            "storm",
            "wind",
            "heat",
            "cold",
        ]
    )
    timeout_seconds: float = 8.0
    read_only: bool = True
    warnings: list[str] = Field(default_factory=list)

    def model_post_init(self, __context: object) -> None:
        if self.market_source_mode is None:
            object.__setattr__(self, "market_source_mode", self.mode)
        else:
            object.__setattr__(self, "mode", self.market_source_mode)
        object.__setattr__(self, "timeout_seconds", self.request_timeout_seconds)

    def validate_safe_defaults(self) -> None:
        if self.request_timeout_seconds > 10:
            raise ValueError("request_timeout_seconds must be <= 10")
        if not self.read_only:
            raise ValueError("read_only must remain enabled")
        if not self.weather_keywords:
            raise ValueError("weather_keywords must not be empty")

    def model_dump_safe(self) -> dict:
        return self.model_dump(mode="json")
