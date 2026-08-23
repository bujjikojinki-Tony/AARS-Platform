from __future__ import annotations

import json
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .models import Candle


BINANCE_SPOT_KLINES = "https://api.binance.com/api/v3/klines"


def fetch_binance_spot_candles(
    symbol: str,
    interval: str = "1h",
    limit: int = 500,
    timeout: float = 10.0,
) -> list[Candle]:
    """Fetch public spot candles. This adapter has no authenticated order path."""
    if not 1 <= limit <= 1000:
        raise ValueError("limit must be between 1 and 1000")
    query = urlencode({"symbol": symbol.upper(), "interval": interval, "limit": limit})
    request = Request(f"{BINANCE_SPOT_KLINES}?{query}", headers={"User-Agent": "AARS-MIL3/0.1"})
    with urlopen(request, timeout=timeout) as response:  # nosec B310: fixed HTTPS endpoint
        payload = json.load(response)
    candles: list[Candle] = []
    for row in payload:
        candles.append(Candle(
            symbol=symbol.upper(),
            timeframe=interval,
            open_time=datetime.fromtimestamp(row[0] / 1000.0, tz=timezone.utc),
            open=float(row[1]),
            high=float(row[2]),
            low=float(row[3]),
            close=float(row[4]),
            volume=float(row[5]),
        ))
    return candles
