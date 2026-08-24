from __future__ import annotations

import argparse
from pathlib import Path

from aars_market.dashboard import write_dashboard_payload
from aars_market.service import DashboardRequest, DashboardService, WINDOWS
from aars_market.storage import MarketStore


def main() -> None:
    parser = argparse.ArgumentParser(description="Archive a PAPER_ONLY Latest Stable View")
    parser.add_argument("--db", default="mil3_market.sqlite")
    parser.add_argument("--symbol", default="SOLUSDT")
    parser.add_argument("--interval", default="1h")
    parser.add_argument("--window", choices=list(WINDOWS), default="90d")
    parser.add_argument("--output-json")
    args = parser.parse_args()

    store = MarketStore(Path(args.db))
    store.init_db()
    payload = DashboardService(store).build(
        DashboardRequest(args.symbol, args.interval, args.window), archive=True
    )
    archive = payload["latest_stable_view_archive"]
    print("execution_mode=PAPER_ONLY")
    print(f"stable_view_id={archive['view_id']} immutable={archive['immutable']}")
    if args.output_json:
        target = write_dashboard_payload(args.output_json, payload)
        print(f"dashboard_payload={target}")


if __name__ == "__main__":
    main()
