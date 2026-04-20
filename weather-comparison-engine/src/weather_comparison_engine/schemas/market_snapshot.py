from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class MarketSnapshot(BaseModel):
    """Normalized read model for the current Polymarket market snapshot."""

    model_config = ConfigDict(extra="allow")

    schema_version: str = Field(default="market_snapshot.v1")
    market_id: str
    market_question: str | None = None
    market_family: str | None = None
    location_name: str | None = None
    updated_at: str | None = None

    market_band: str | None = None
    market_band_label: str | None = None
    market_band_scheme: str | None = None

    favored_side: str | None = None
    market_probability: float | None = None
    yes_price: float | None = None
    no_price: float | None = None
    liquidity: float | None = None
    volume_24hr: float | None = None

