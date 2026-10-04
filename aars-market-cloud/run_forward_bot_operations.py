from __future__ import annotations

import argparse
import json
from pathlib import Path

from aars_market.forward_ops import (
    build_forward_bot_operations_view,
    run_forward_bot_scheduler,
    run_forward_bot_wake,
)
from aars_market.storage import MarketStore


def _print(payload: object) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run MIL-3.25 closed-bar PAPER_ONLY forward bot operations"
    )
    parser.add_argument("--db", default="mil3_market.sqlite")
    parser.add_argument("--action", choices=("STATUS", "WAKE", "FOREGROUND"), required=True)
    parser.add_argument("--sandbox-id", default="aars-paper-sandbox")
    parser.add_argument("--worker-id", default="aars-forward-bot-worker")
    parser.add_argument("--lease-seconds", type=int, default=120)
    parser.add_argument("--poll-seconds", type=float, default=60.0)
    parser.add_argument("--max-wakes", type=int, default=0)
    args = parser.parse_args()

    store = MarketStore(Path(args.db))
    store.init_db()
    if args.action == "STATUS":
        result = build_forward_bot_operations_view(store, args.sandbox_id)
    elif args.action == "WAKE":
        result = run_forward_bot_wake(
            store,
            args.sandbox_id,
            worker_id=args.worker_id,
            lease_seconds=args.lease_seconds,
        )
    else:
        max_wakes = None if args.max_wakes == 0 else args.max_wakes
        try:
            result = run_forward_bot_scheduler(
                store,
                args.sandbox_id,
                poll_seconds=args.poll_seconds,
                max_wakes=max_wakes,
                worker_id=args.worker_id,
                lease_seconds=args.lease_seconds,
                on_wake=_print,
            )
        except KeyboardInterrupt:
            result = {
                "schema_version": "mil3.forward-bot-scheduler-stop.v1",
                "execution_mode": "PAPER_ONLY",
                "status": "STOPPED_BY_USER",
                "external_order_requests_created": False,
                "order_path_present": False,
                "live_execution_allowed": False,
            }
    _print(result)


if __name__ == "__main__":
    main()
