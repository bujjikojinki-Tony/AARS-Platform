from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

from aars_market.adapters import fetch_binance_spot_history
from aars_market.storage import MarketStore


DEFAULT_SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")


def main() -> None:
    parser = argparse.ArgumentParser(description="AARS MIL-3.1 public market ingestion")
    parser.add_argument("--db", default="mil3_market.sqlite", help="SQLite database path")
    parser.add_argument("--interval", default="1h")
    parser.add_argument("--days", type=int, default=120)
    parser.add_argument("--symbols", nargs="+", default=list(DEFAULT_SYMBOLS))
    args = parser.parse_args()

    if args.days <= 0:
        raise SystemExit("--days must be positive")

    store = MarketStore(Path(args.db))
    store.init_db()
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=args.days)

    print("execution_mode=PAPER_ONLY")
    print(f"database={args.db} interval={args.interval} window_days={args.days}")

    for symbol in args.symbols:
        candles = fetch_binance_spot_history(
            symbol=symbol,
            interval=args.interval,
            start=start,
            end=end,
        )
        count = store.upsert_candles(candles, source="binance_spot_public")
        latest = store.latest_open_time(symbol, args.interval)
        fresh = store.is_fresh(
            symbol,
            args.interval,
            now=end,
            max_age=timedelta(hours=2),
        )
        print(
            f"{symbol}: fetched={len(candles)} upserted={count} "
            f"stored={store.count_candles(symbol, args.interval)} "
            f"latest={latest.isoformat() if latest else None} fresh={fresh}"
        )


if __name__ == "__main__":
    main()
