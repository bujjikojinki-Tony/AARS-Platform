from __future__ import annotations

from enum import Enum
from typing import Any
from typing import Literal

from pydantic import BaseModel
from pydantic import Field

from .core import now_iso
from .core import MarketSnapshot


class _CallableBool:
    def __init__(self, value: bool) -> None:
        self.value = bool(value)

    def __call__(self) -> bool:
        return self.value

    def __bool__(self) -> bool:
        return self.value

    def __repr__(self) -> str:
        return "True" if self.value else "False"


class PolymarketConnectorMode(str, Enum):
    MOCK_ONLY = "MOCK_ONLY"
    POLYMARKET_ONLY = "POLYMARKET_ONLY"
    HYBRID = "HYBRID"


MarketSourceMode = PolymarketConnectorMode


class PolymarketMarketRecord(BaseModel):
    polymarket_market_id: str | None = None
    market_id: str | None = None
    condition_id: str | None = None
    question: str
    slug: str | None = None
    category: str | None = None
    active: bool | None = None
    closed: bool | None = None
    archived: bool | None = None
    end_date: str | None = None
    resolution_source: str | None = None
    outcomes: list[str] = Field(default_factory=list)
    outcome_prices: list[float] = Field(default_factory=list)
    clob_token_ids: list[str] = Field(default_factory=list)
    liquidity: float | None = None
    volume: float | None = None
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    fetched_at: str = Field(default_factory=now_iso)
    source: str = "polymarket"
    binary: bool | None = Field(default=None, alias="is_binary")
    is_closed: bool | None = None
    is_active: bool | None = None

    def model_post_init(self, __context: Any) -> None:
        identifier = self.market_id or self.polymarket_market_id
        if not identifier:
            raise ValueError("either market_id or polymarket_market_id is required")
        object.__setattr__(self, "market_id", identifier)
        object.__setattr__(self, "polymarket_market_id", identifier)

        binary = self.binary
        if binary is None:
            binary = len(self.outcomes) == 2
        object.__setattr__(self, "binary", bool(binary))

        closed = self.closed if self.closed is not None else self.is_closed
        if closed is None:
            closed = False
        closed = bool(closed)
        object.__setattr__(self, "closed", closed)
        object.__setattr__(self, "is_closed", closed)

        active = self.active if self.active is not None else self.is_active
        if active is None:
            active = not closed
        active = bool(active)
        object.__setattr__(self, "active", active)
        object.__setattr__(self, "is_active", active)

    @property
    def is_binary(self) -> _CallableBool:
        return _CallableBool(bool(self.binary))

    def yes_price(self) -> float | None:
        return self._price_for_outcome(("yes", "YES"), 0)

    def no_price(self) -> float | None:
        return self._price_for_outcome(("no", "NO"), 1)

    def to_market_snapshot(self, spread: float | None = None) -> MarketSnapshot:
        yes_price = self.yes_price()
        no_price = self.no_price()
        if spread is None and yes_price is not None and no_price is not None:
            spread = abs(yes_price - no_price)
        market_id = self.condition_id or self.market_id or self.polymarket_market_id or "unknown_market"
        return MarketSnapshot(
            market_id=market_id,
            question=self.question,
            yes_price=yes_price if yes_price is not None else 0.0,
            no_price=no_price if no_price is not None else 0.0,
            liquidity=float(self.liquidity or 0.0),
            spread=float(spread or 0.0),
            source="polymarket",
            fetched_at=self.fetched_at,
        )

    def model_dump(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        data = super().model_dump(*args, **kwargs)
        data["market_id"] = self.market_id
        data["polymarket_market_id"] = self.polymarket_market_id
        data["is_binary"] = self.is_binary()
        data["is_closed"] = bool(self.is_closed)
        data["is_active"] = bool(self.is_active)
        return data

    def _price_for_outcome(self, target_labels: tuple[str, str], fallback_index: int) -> float | None:
        if len(self.outcomes) != len(self.outcome_prices) or not self.outcome_prices:
            return self.outcome_prices[fallback_index] if len(self.outcome_prices) > fallback_index else None
        for index, outcome in enumerate(self.outcomes):
            normalized = str(outcome).strip().lower()
            if normalized in {label.lower() for label in target_labels}:
                try:
                    return float(self.outcome_prices[index])
                except Exception:
                    return None
        if len(self.outcome_prices) > fallback_index:
            try:
                return float(self.outcome_prices[fallback_index])
            except Exception:
                return None
        return None


class PolymarketConnectorHealth(BaseModel):
    connector_id: Literal["polymarket_read_only_v0"] = "polymarket_read_only_v0"
    gamma_reachable: bool = False
    clob_reachable: bool = False
    last_gamma_status: int | None = None
    last_clob_status: int | None = None
    mode: PolymarketConnectorMode = PolymarketConnectorMode.MOCK_ONLY
    warnings: list[str] = Field(default_factory=list)
    last_checked_at: str = Field(default_factory=now_iso)
    status: str = "UNKNOWN"
    allow_polymarket_network: bool = False
    read_only: bool = True
    updated_at: str = Field(default_factory=now_iso)


class PolymarketPriceRecord(BaseModel):
    market_id: str
    token_id: str | None = None
    outcome: Literal["YES", "NO", "UNKNOWN"]
    price: float | None = None
    midpoint: float | None = None
    spread: float | None = None
    source: Literal[
        "CLOB_PRICE",
        "CLOB_MIDPOINT",
        "CLOB_SPREAD",
        "GAMMA_OUTCOME_PRICE",
    ]
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    fetched_at: str = Field(default_factory=now_iso)
