from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from .dashboard import build_dashboard_payload
from .storage import MarketStore


DEFAULT_SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
WINDOWS: dict[str, timedelta | None] = {
    "30d": timedelta(days=30),
    "90d": timedelta(days=90),
    "180d": timedelta(days=180),
    "365d": timedelta(days=365),
    "all": None,
}


@dataclass(frozen=True)
class DashboardRequest:
    symbol: str = "SOLUSDT"
    timeframe: str = "1h"
    replay_window: str = "90d"


class DashboardService:
    """Orchestration over persisted market data and PAPER_ONLY shadow replay."""

    def __init__(self, store: MarketStore, *, warmup_bars: int = 120) -> None:
        self.store = store
        self.warmup_bars = warmup_bars

    def markets(self) -> list[dict[str, object]]:
        return self.store.list_markets()

    def build(
        self,
        request: DashboardRequest,
        *,
        now: datetime | None = None,
        archive: bool = True,
    ) -> dict[str, Any]:
        symbol = request.symbol.upper()
        if symbol not in DEFAULT_SYMBOLS:
            raise ValueError(f"unsupported symbol: {symbol}")
        if request.replay_window not in WINDOWS:
            raise ValueError(f"unsupported replay window: {request.replay_window}")
        current = now or datetime.now(timezone.utc)
        duration = WINDOWS[request.replay_window]
        latest = self.store.latest_open_time(symbol, request.timeframe)
        if latest is None:
            raise ValueError(f"no candles stored for {symbol} {request.timeframe}")
        start = latest - duration if duration is not None else None
        candles = self.store.load_candles(symbol, request.timeframe, start=start, end=latest)
        if len(candles) <= self.warmup_bars:
            raise ValueError(
                f"need > {self.warmup_bars} candles for {symbol} {request.timeframe} "
                f"window={request.replay_window}; stored={len(candles)}"
            )
        funding = self.store.load_funding_rates(
            symbol,
            start=candles[0].open_time,
            end=candles[-1].open_time,
        )
        payload = build_dashboard_payload(
            candles,
            warmup_bars=self.warmup_bars,
            funding_rates=funding,
            data_fresh=self.store.is_fresh(symbol, request.timeframe, now=current),
            source="SQLite normalized Binance public market data",
            generated_at=current,
        )
        payload["selection"] = {
            "symbol": symbol,
            "timeframe": request.timeframe,
            "replay_window": request.replay_window,
        }
        payload["available_markets"] = self.markets()
        payload["available_windows"] = list(WINDOWS)
        if archive:
            view_id = self.store.archive_latest_stable_view(
                payload, replay_window=request.replay_window, created_at=current
            )
            payload["latest_stable_view_archive"] = {
                "view_id": view_id,
                "archived_at": current.astimezone(timezone.utc).isoformat(),
                "immutable": True,
            }
        else:
            payload["latest_stable_view_archive"] = None
        return payload
