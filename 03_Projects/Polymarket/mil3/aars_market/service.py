from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from .dashboard import build_dashboard_payload
from .portfolio import build_portfolio_payload
from .stable_diff import compare_stable_views
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


@dataclass(frozen=True)
class PortfolioRequest:
    symbols: tuple[str, ...] = DEFAULT_SYMBOLS
    timeframe: str = "1h"
    replay_window: str = "90d"
    strategy: str = "AARS_DYNAMIC"


class DashboardService:
    """Orchestration over persisted market data and PAPER_ONLY shadow replay."""

    def __init__(self, store: MarketStore, *, warmup_bars: int = 120) -> None:
        self.store = store
        self.warmup_bars = warmup_bars

    def markets(self) -> list[dict[str, object]]:
        return self.store.list_markets()

    def funding_cadence(self, symbol: str) -> dict[str, Any]:
        normalized = symbol.upper()
        if normalized not in DEFAULT_SYMBOLS:
            raise ValueError(f"unsupported symbol: {normalized}")
        observations = self.store.load_funding_cadence_observations(normalized)
        history = [
            {
                "symbol": item.symbol,
                "observed_at": item.observed_at.astimezone(timezone.utc).isoformat(),
                "interval_hours": item.interval_hours,
                "adjusted_rate_cap": item.adjusted_rate_cap,
                "adjusted_rate_floor": item.adjusted_rate_floor,
                "disclaimer": item.disclaimer,
                "source_status": item.source_status,
            }
            for item in observations
        ]
        current = history[-1] if history else {
            "symbol": normalized,
            "observed_at": None,
            "interval_hours": 8,
            "adjusted_rate_cap": None,
            "adjusted_rate_floor": None,
            "disclaimer": False,
            "source_status": "DEFAULT_8H_FALLBACK",
        }
        return {
            "schema_version": "mil3.funding-cadence.v1",
            "execution_mode": "PAPER_ONLY",
            "current": current,
            "observations": history,
        }

    def build(
        self,
        request: DashboardRequest,
        *,
        now: datetime | None = None,
        archive: bool = True,
        max_trace_points: int = 240,
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
        cadence_observations = self.store.load_funding_cadence_observations(
            symbol,
            start=candles[self.warmup_bars - 1].open_time,
            end=candles[-1].open_time,
            include_previous=True,
        )
        payload = build_dashboard_payload(
            candles,
            warmup_bars=self.warmup_bars,
            funding_rates=funding,
            funding_cadence_observations=cadence_observations,
            data_fresh=self.store.is_fresh(symbol, request.timeframe, now=current),
            source="SQLite normalized Binance public market data",
            generated_at=current,
            max_trace_points=max_trace_points,
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

    def build_portfolio(
        self,
        request: PortfolioRequest,
        *,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        current = now or datetime.now(timezone.utc)
        symbols = tuple(symbol.upper() for symbol in request.symbols)
        if not symbols:
            raise ValueError("portfolio symbols must not be empty")
        if len(set(symbols)) != len(symbols):
            raise ValueError("portfolio symbols must be unique")
        payloads = [
            self.build(
                DashboardRequest(symbol, request.timeframe, request.replay_window),
                now=current,
                archive=False,
                max_trace_points=1_000_000,
            )
            for symbol in symbols
        ]
        payload = build_portfolio_payload(
            payloads,
            strategy_id=request.strategy,
            generated_at=current,
        )
        payload["selection"] = {
            "symbols": list(symbols),
            "timeframe": request.timeframe,
            "replay_window": request.replay_window,
        }
        return payload

    def compare_views(self, before_id: str, after_id: str) -> dict[str, Any]:
        before = self.store.get_latest_stable_view(before_id)
        after = self.store.get_latest_stable_view(after_id)
        if before is None:
            raise ValueError(f"stable view not found: {before_id}")
        if after is None:
            raise ValueError(f"stable view not found: {after_id}")
        before_market = before.get("market", {})
        after_market = after.get("market", {})
        if (
            before_market.get("symbol"),
            before_market.get("timeframe"),
        ) != (
            after_market.get("symbol"),
            after_market.get("timeframe"),
        ):
            raise ValueError("stable views must use the same symbol and timeframe")
        return compare_stable_views(
            before,
            after,
            before_id=before_id,
            after_id=after_id,
        )

    def list_shadow_snapshots(
        self, *, limit: int = 30, target_strategy: str | None = None
    ) -> dict[str, Any]:
        return {
            "schema_version": "mil3.shadow-daily-index.v1",
            "execution_mode": "PAPER_ONLY",
            "shadow_snapshots": self.store.list_shadow_daily_snapshots(
                limit=limit, target_strategy=target_strategy
            ),
            "read_only": True,
        }

    def shadow_snapshot(self, snapshot_id: str) -> dict[str, Any]:
        payload = self.store.get_shadow_daily_snapshot(snapshot_id)
        if payload is None:
            raise KeyError(f"shadow snapshot not found: {snapshot_id}")
        return payload

    def shadow_stability(
        self, *, limit: int = 90, target_strategy: str | None = None
    ) -> dict[str, Any]:
        # Local import avoids coupling the base dashboard path to validation code.
        from .shadow import build_shadow_stability

        snapshots = self.store.load_shadow_daily_snapshots(
            limit=limit, target_strategy=target_strategy
        )
        return build_shadow_stability(snapshots)
