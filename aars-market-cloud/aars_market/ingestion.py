from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable, Sequence

from .adapters import (
    fetch_binance_funding_history,
    fetch_binance_funding_info,
    fetch_binance_spot_history,
)
from .models import Candle, FundingCadenceObservation, FundingRate
from .service import DEFAULT_SYMBOLS
from .storage import MarketStore


EXECUTION_MODE = "PAPER_ONLY"
CandleFetcher = Callable[..., list[Candle]]
FundingFetcher = Callable[..., list[FundingRate]]
FundingInfoFetcher = Callable[..., list[FundingCadenceObservation]]


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def materialize_funding_cadence_snapshot(
    adjusted: Sequence[FundingCadenceObservation],
    symbols: Sequence[str],
    observed_at: datetime,
) -> list[FundingCadenceObservation]:
    """Build a complete, timestamped cadence snapshot for configured symbols."""
    observed = _utc(observed_at)
    configured = {symbol.upper() for symbol in symbols}
    adjusted_by_symbol = {
        item.symbol.upper(): item
        for item in adjusted
        if item.symbol.upper() in configured
    }
    return [
        FundingCadenceObservation(
            symbol=symbol.upper(),
            observed_at=observed,
            interval_hours=item.interval_hours,
            adjusted_rate_cap=item.adjusted_rate_cap,
            adjusted_rate_floor=item.adjusted_rate_floor,
            disclaimer=item.disclaimer,
            source_status=item.source_status,
        )
        if (item := adjusted_by_symbol.get(symbol.upper())) is not None
        else FundingCadenceObservation(
            symbol=symbol.upper(),
            observed_at=observed,
            interval_hours=8,
            source_status="DEFAULT_ABSENT",
        )
        for symbol in symbols
    ]


@dataclass(frozen=True)
class ResourceIngestion:
    resource: str
    symbol: str
    start: str
    end: str
    fetched: int
    upserted: int
    status: str
    error: str | None = None
    details: dict[str, object] | None = None


class IncrementalIngestor:
    """Incrementally refresh public candles and funding with an overlap repair window."""

    def __init__(
        self,
        store: MarketStore,
        *,
        symbols: Sequence[str] = DEFAULT_SYMBOLS,
        timeframe: str = "1h",
        bootstrap_days: int = 120,
        candle_overlap: timedelta = timedelta(hours=2),
        funding_overlap: timedelta = timedelta(hours=8),
        candle_fetcher: CandleFetcher = fetch_binance_spot_history,
        funding_fetcher: FundingFetcher = fetch_binance_funding_history,
        funding_info_fetcher: FundingInfoFetcher = fetch_binance_funding_info,
    ) -> None:
        if bootstrap_days <= 0:
            raise ValueError("bootstrap_days must be positive")
        if candle_overlap < timedelta(0) or funding_overlap < timedelta(0):
            raise ValueError("overlap windows must be non-negative")
        self.store = store
        self.symbols = tuple(symbol.upper() for symbol in symbols)
        self.timeframe = timeframe
        self.bootstrap_days = bootstrap_days
        self.candle_overlap = candle_overlap
        self.funding_overlap = funding_overlap
        self.candle_fetcher = candle_fetcher
        self.funding_fetcher = funding_fetcher
        self.funding_info_fetcher = funding_info_fetcher

    def _start(self, latest: datetime | None, overlap: timedelta, end: datetime) -> datetime:
        return latest - overlap if latest is not None else end - timedelta(days=self.bootstrap_days)

    def run_cycle(self, *, now: datetime | None = None) -> dict[str, object]:
        started = _utc(now or datetime.now(timezone.utc))
        records: list[ResourceIngestion] = []
        try:
            adjusted = self.funding_info_fetcher(observed_at=started)
            observations = materialize_funding_cadence_snapshot(
                adjusted, self.symbols, started
            )
            upserted = self.store.upsert_funding_cadence_observations(
                observations,
                source="binance_usdm_public_funding_info",
            )
            records.append(
                ResourceIngestion(
                    "funding_info",
                    "MULTI_ASSET",
                    started.isoformat(),
                    started.isoformat(),
                    len(adjusted),
                    upserted,
                    "SUCCESS",
                    details={
                        item.symbol: {
                            "interval_hours": item.interval_hours,
                            "source_status": item.source_status,
                        }
                        for item in observations
                    },
                )
            )
        except Exception as exc:
            records.append(
                ResourceIngestion(
                    "funding_info",
                    "MULTI_ASSET",
                    started.isoformat(),
                    started.isoformat(),
                    0,
                    0,
                    "FAILED",
                    f"{type(exc).__name__}: {exc}",
                )
            )
        for symbol in self.symbols:
            candle_start = self._start(
                self.store.latest_open_time(symbol, self.timeframe), self.candle_overlap, started
            )
            try:
                candles = self.candle_fetcher(symbol, self.timeframe, candle_start, started)
                upserted = self.store.upsert_candles(candles, source="binance_spot_public_incremental")
                records.append(
                    ResourceIngestion(
                        "candles", symbol, candle_start.isoformat(), started.isoformat(),
                        len(candles), upserted, "SUCCESS",
                    )
                )
            except Exception as exc:
                records.append(
                    ResourceIngestion(
                        "candles", symbol, candle_start.isoformat(), started.isoformat(),
                        0, 0, "FAILED", f"{type(exc).__name__}: {exc}",
                    )
                )

            funding_start = self._start(
                self.store.latest_funding_time(symbol), self.funding_overlap, started
            )
            try:
                funding = self.funding_fetcher(symbol, funding_start, started)
                upserted = self.store.upsert_funding_rates(
                    funding, source="binance_usdm_public_incremental"
                )
                records.append(
                    ResourceIngestion(
                        "funding", symbol, funding_start.isoformat(), started.isoformat(),
                        len(funding), upserted, "SUCCESS",
                    )
                )
            except Exception as exc:
                records.append(
                    ResourceIngestion(
                        "funding", symbol, funding_start.isoformat(), started.isoformat(),
                        0, 0, "FAILED", f"{type(exc).__name__}: {exc}",
                    )
                )

        failures = sum(record.status == "FAILED" for record in records)
        status = "SUCCESS" if failures == 0 else "FAILED" if failures == len(records) else "PARTIAL"
        finished = _utc(now or datetime.now(timezone.utc))
        summary: dict[str, object] = {
            "execution_mode": EXECUTION_MODE,
            "started_at": started.isoformat(),
            "finished_at": finished.isoformat(),
            "status": status,
            "resources": [asdict(record) for record in records],
        }
        summary["cycle_id"] = self.store.record_ingestion_cycle(summary)
        return summary


def run_scheduler(
    ingestor: IncrementalIngestor,
    *,
    interval_seconds: float,
    max_cycles: int | None = None,
    clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    sleeper: Callable[[float], None] = time.sleep,
    on_cycle: Callable[[dict[str, object]], None] | None = None,
) -> list[dict[str, object]]:
    if interval_seconds <= 0:
        raise ValueError("interval_seconds must be positive")
    if max_cycles is not None and max_cycles <= 0:
        raise ValueError("max_cycles must be positive when supplied")
    completed: list[dict[str, object]] = []
    while max_cycles is None or len(completed) < max_cycles:
        summary = ingestor.run_cycle(now=clock())
        completed.append(summary)
        if on_cycle is not None:
            on_cycle(summary)
        if max_cycles is not None and len(completed) >= max_cycles:
            break
        sleeper(interval_seconds)
    return completed
