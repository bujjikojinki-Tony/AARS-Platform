from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

from aars_market.adapters import fetch_binance_funding_history, fetch_binance_funding_info
from aars_market.ingestion import materialize_funding_cadence_snapshot
from aars_market.service import DEFAULT_SYMBOLS
from aars_market.storage import MarketStore


def main() -> None:
    parser = argparse.ArgumentParser(
        description="AARS MIL-3.9 public funding-history and cadence ingestion"
    )
    parser.add_argument("--db", default="mil3_market.sqlite")
    parser.add_argument("--days", type=int, default=365)
    parser.add_argument("--symbols", nargs="+", default=list(DEFAULT_SYMBOLS))
    args = parser.parse_args()
    if args.days <= 0:
        raise SystemExit("--days must be positive")

    store = MarketStore(Path(args.db))
    store.init_db()
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=args.days)
    print("execution_mode=PAPER_ONLY")
    print("source=BINANCE_USDM_PUBLIC_FUNDING_HISTORY")
    for symbol in args.symbols:
        rates = fetch_binance_funding_history(symbol, start, end)
        count = store.upsert_funding_rates(rates, source="binance_usdm_public")
        print(f"{symbol.upper()}: fetched={len(rates)} upserted={count} stored={store.count_funding_rates(symbol)}")

    adjusted = fetch_binance_funding_info(observed_at=end)
    observations = materialize_funding_cadence_snapshot(adjusted, args.symbols, end)
    cadence_count = store.upsert_funding_cadence_observations(
        observations, source="binance_usdm_public_funding_info"
    )
    print("source=BINANCE_USDM_PUBLIC_FUNDING_INFO")
    print(f"cadence_snapshot: adjusted={len(adjusted)} upserted={cadence_count}")
    for observation in observations:
        print(
            f"{observation.symbol}: interval_hours={observation.interval_hours} "
            f"status={observation.source_status}"
        )


if __name__ == "__main__":
    main()
