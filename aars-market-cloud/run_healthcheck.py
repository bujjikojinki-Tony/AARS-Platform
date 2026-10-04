from __future__ import annotations

import argparse
from datetime import timedelta

from aars_market.operations import HEALTH_EXIT_CODES, assess_operational_health, dumps
from aars_market.service import DEFAULT_SYMBOLS


def main() -> None:
    parser = argparse.ArgumentParser(description="AARS MIL-3.10 read-only operational health check")
    parser.add_argument("--db", default="mil3_market.sqlite")
    parser.add_argument("--interval", default="1h")
    parser.add_argument("--symbols", nargs="+", default=list(DEFAULT_SYMBOLS))
    parser.add_argument("--max-cycle-age-seconds", type=float, default=7200)
    parser.add_argument("--max-candle-age-seconds", type=float, default=7200)
    args = parser.parse_args()
    payload = assess_operational_health(
        args.db,
        symbols=args.symbols,
        timeframe=args.interval,
        max_cycle_age=timedelta(seconds=args.max_cycle_age_seconds),
        max_candle_age=timedelta(seconds=args.max_candle_age_seconds),
    )
    print(dumps(payload))
    raise SystemExit(HEALTH_EXIT_CODES[str(payload["status"])])


if __name__ == "__main__":
    main()
