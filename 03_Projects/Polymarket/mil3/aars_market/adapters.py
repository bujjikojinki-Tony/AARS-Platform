from __future__ import annotations

import json
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .models import Candle, FundingRate


BINANCE_SPOT_KLINES = "https://api.binance.com/api/v3/klines"
BINANCE_USDM_FUNDING = "https://fapi.binance.com/fapi/v1/fundingRate"


def _to_ms(value: datetime) -> int:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return int(value.astimezone(timezone.utc).timestamp() * 1000)


def _decode_klines(payload: list[list[object]], symbol: str, interval: str) -> list[Candle]:
    candles: list[Candle] = []
    for row in payload:
        candles.append(
            Candle(
                symbol=symbol.upper(),
                timeframe=interval,
                open_time=datetime.fromtimestamp(float(row[0]) / 1000.0, tz=timezone.utc),
                open=float(row[1]),
                high=float(row[2]),
                low=float(row[3]),
                close=float(row[4]),
                volume=float(row[5]),
            )
        )
    return candles


def _request_klines(params: dict[str, object], timeout: float) -> list[list[object]]:
    request = Request(
        f"{BINANCE_SPOT_KLINES}?{urlencode(params)}",
        headers={"User-Agent": "AARS-MIL3/0.2"},
    )
    with urlopen(request, timeout=timeout) as response:  # nosec B310: fixed HTTPS endpoint
        payload = json.load(response)
    if not isinstance(payload, list):
        raise RuntimeError("unexpected Binance kline response")
    return payload


def _decode_funding(payload: list[dict[str, object]], symbol: str) -> list[FundingRate]:
    return [
        FundingRate(
            symbol=str(row.get("symbol", symbol)).upper(),
            funding_time=datetime.fromtimestamp(float(row["fundingTime"]) / 1000.0, tz=timezone.utc),
            funding_rate=float(row["fundingRate"]),
            mark_price=float(row["markPrice"]) if row.get("markPrice") not in (None, "") else None,
            rate_type=str(row.get("rateType", "Regular")),
        )
        for row in payload
    ]


def _request_funding(params: dict[str, object], timeout: float) -> list[dict[str, object]]:
    request = Request(
        f"{BINANCE_USDM_FUNDING}?{urlencode(params)}",
        headers={"User-Agent": "AARS-MIL3/0.3"},
    )
    with urlopen(request, timeout=timeout) as response:  # nosec B310: fixed HTTPS endpoint
        payload = json.load(response)
    if not isinstance(payload, list):
        raise RuntimeError("unexpected Binance funding response")
    return payload


def fetch_binance_spot_candles(
    symbol: str,
    interval: str = "1h",
    limit: int = 500,
    timeout: float = 10.0,
) -> list[Candle]:
    """Fetch latest public spot candles. No authenticated order path exists."""
    if not 1 <= limit <= 1000:
        raise ValueError("limit must be between 1 and 1000")
    payload = _request_klines(
        {"symbol": symbol.upper(), "interval": interval, "limit": limit},
        timeout,
    )
    return _decode_klines(payload, symbol, interval)


def fetch_binance_spot_history(
    symbol: str,
    interval: str,
    start: datetime,
    end: datetime | None = None,
    *,
    timeout: float = 10.0,
    max_pages: int = 100,
) -> list[Candle]:
    """Fetch historical public spot candles with deterministic pagination.

    Pagination advances by the returned candle open timestamp + 1 ms. The
    caller controls max_pages so a configuration error cannot create an
    unbounded network loop.
    """
    if max_pages <= 0:
        raise ValueError("max_pages must be positive")
    start_ms = _to_ms(start)
    end_ms = _to_ms(end) if end is not None else None
    if end_ms is not None and end_ms < start_ms:
        raise ValueError("end must be at or after start")

    result: list[Candle] = []
    cursor = start_ms
    for _ in range(max_pages):
        params: dict[str, object] = {
            "symbol": symbol.upper(),
            "interval": interval,
            "limit": 1000,
            "startTime": cursor,
        }
        if end_ms is not None:
            params["endTime"] = end_ms
        payload = _request_klines(params, timeout)
        if not payload:
            break
        batch = _decode_klines(payload, symbol, interval)
        result.extend(batch)
        last_open_ms = int(batch[-1].open_time.timestamp() * 1000)
        next_cursor = last_open_ms + 1
        if next_cursor <= cursor:
            raise RuntimeError("Binance pagination did not advance")
        cursor = next_cursor
        if len(payload) < 1000 or (end_ms is not None and cursor > end_ms):
            break
    else:
        raise RuntimeError("historical fetch reached max_pages safety limit")

    # Defensive de-duplication while preserving chronological order.
    unique: dict[datetime, Candle] = {c.open_time: c for c in result}
    return [unique[key] for key in sorted(unique)]


def fetch_binance_funding_history(
    symbol: str,
    start: datetime,
    end: datetime | None = None,
    *,
    timeout: float = 10.0,
    max_pages: int = 100,
) -> list[FundingRate]:
    """Fetch public USD-M funding events in ascending order, without authentication."""
    if max_pages <= 0:
        raise ValueError("max_pages must be positive")
    start_ms = _to_ms(start)
    end_ms = _to_ms(end) if end is not None else None
    if end_ms is not None and end_ms < start_ms:
        raise ValueError("end must be at or after start")

    result: list[FundingRate] = []
    cursor = start_ms
    for _ in range(max_pages):
        params: dict[str, object] = {"symbol": symbol.upper(), "limit": 1000, "startTime": cursor}
        if end_ms is not None:
            params["endTime"] = end_ms
        payload = _request_funding(params, timeout)
        if not payload:
            break
        batch = _decode_funding(payload, symbol)
        result.extend(batch)
        last_ms = int(batch[-1].funding_time.timestamp() * 1000)
        next_cursor = last_ms + 1
        if next_cursor <= cursor:
            raise RuntimeError("Binance funding pagination did not advance")
        cursor = next_cursor
        if len(payload) < 1000 or (end_ms is not None and cursor > end_ms):
            break
    else:
        raise RuntimeError("funding fetch reached max_pages safety limit")

    unique = {(item.symbol, item.funding_time, item.rate_type): item for item in result}
    return sorted(unique.values(), key=lambda item: (item.funding_time, item.rate_type))
