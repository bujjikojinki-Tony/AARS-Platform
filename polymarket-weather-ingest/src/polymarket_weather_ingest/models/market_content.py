from pydantic import BaseModel


class MarketContent(BaseModel):
    event_id: str | None = None
    event_title: str | None = None

    market_id: str | None = None
    market_question: str | None = None
    market_slug: str | None = None

    category: str | None = None
    active: bool | None = None
    closed: bool | None = None

    volume_24hr: float | None = None
    liquidity: float | None = None
