from __future__ import annotations

import argparse
import json
from pathlib import Path

from aars_market.forward_monitor import ForwardMonitorSettings, run_forward_monitor
from aars_market.storage import MarketStore


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the MIL-3.18 local PAPER_ONLY forward checkpoint monitor"
    )
    parser.add_argument("--db", default="mil3_market.sqlite")
    parser.add_argument("--poll-seconds", type=float, default=3600.0)
    parser.add_argument("--max-cycles", type=int, default=0, help="0 runs until interrupted")
    parser.add_argument("--minimum-forward-bars", type=int, default=24)
    parser.add_argument("--confirmation-bars", type=int, default=168)
    parser.add_argument("--trial-limit", type=int, default=100)
    args = parser.parse_args()

    store = MarketStore(Path(args.db))
    store.init_db()
    print("execution_mode=PAPER_ONLY")
    print("monitor_scope=IMMUTABLE_FORWARD_OBSERVATION_ONLY")
    print("observation_application_allowed=false")
    print("automatic_strategy_change_allowed=false")
    print("live_execution_allowed=false")
    try:
        run_forward_monitor(
            store,
            interval_seconds=args.poll_seconds,
            max_cycles=args.max_cycles or None,
            settings=ForwardMonitorSettings(
                minimum_forward_bars=args.minimum_forward_bars,
                confirmation_bars=args.confirmation_bars,
                trial_limit=args.trial_limit,
            ),
            on_cycle=lambda summary: print(json.dumps(summary, sort_keys=True)),
        )
    except KeyboardInterrupt:
        print("monitor_status=STOPPED_BY_USER")


if __name__ == "__main__":
    main()
