from __future__ import annotations

import argparse
import json
from pathlib import Path

from aars_market.ingestion import IncrementalIngestor, run_scheduler
from aars_market.service import DEFAULT_SYMBOLS
from aars_market.storage import MarketStore


def main() -> None:
    parser = argparse.ArgumentParser(description="AARS MIL-3.8 incremental public-data scheduler")
    parser.add_argument("--db", default="mil3_market.sqlite")
    parser.add_argument("--interval", default="1h")
    parser.add_argument("--poll-seconds", type=float, default=3600.0)
    parser.add_argument("--max-cycles", type=int, default=0, help="0 runs until interrupted")
    parser.add_argument("--bootstrap-days", type=int, default=120)
    parser.add_argument("--symbols", nargs="+", default=list(DEFAULT_SYMBOLS))
    args = parser.parse_args()

    store = MarketStore(Path(args.db))
    store.init_db()
    ingestor = IncrementalIngestor(
        store,
        symbols=args.symbols,
        timeframe=args.interval,
        bootstrap_days=args.bootstrap_days,
    )
    print("execution_mode=PAPER_ONLY")
    print("scheduler_scope=PUBLIC_MARKET_DATA_ONLY")
    try:
        run_scheduler(
            ingestor,
            interval_seconds=args.poll_seconds,
            max_cycles=args.max_cycles or None,
            on_cycle=lambda summary: print(json.dumps(summary, sort_keys=True)),
        )
    except KeyboardInterrupt:
        print("scheduler_status=STOPPED_BY_USER")


if __name__ == "__main__":
    main()
