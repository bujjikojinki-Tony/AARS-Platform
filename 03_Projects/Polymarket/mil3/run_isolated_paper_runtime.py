from __future__ import annotations

import argparse
import json
from pathlib import Path

from aars_market.isolated_runtime import (
    IsolatedRuntimeSettings,
    run_isolated_paper_runtime,
)
from aars_market.storage import MarketStore


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Govern the MIL-3.22 fenced isolated PAPER_ONLY runtime"
    )
    parser.add_argument("--db", default="mil3_market.sqlite")
    parser.add_argument(
        "--action",
        required=True,
        choices=("RUN", "STOP", "ARM_KILL", "CLEAR_KILL", "RECONCILE"),
    )
    parser.add_argument("--sandbox-id", default="aars-paper-sandbox")
    parser.add_argument("--session-id")
    parser.add_argument("--worker-id", default="aars-local-paper-worker")
    parser.add_argument("--operator")
    parser.add_argument("--note")
    parser.add_argument("--lease-seconds", type=int, default=30)
    parser.add_argument("--heartbeat-interval-seconds", type=float, default=10.0)
    parser.add_argument("--max-cycles", type=int, default=1)
    args = parser.parse_args()

    store = MarketStore(Path(args.db))
    store.init_db()
    if args.action == "RUN":
        result = run_isolated_paper_runtime(
            store,
            args.sandbox_id,
            worker_id=args.worker_id,
            settings=IsolatedRuntimeSettings(
                lease_seconds=args.lease_seconds,
                heartbeat_interval_seconds=args.heartbeat_interval_seconds,
                max_cycles=args.max_cycles,
            ),
        )
    elif args.action == "STOP":
        if not args.session_id or not args.operator or not args.note:
            parser.error("--session-id, --operator and --note are required for STOP")
        event_id = store.stop_isolated_paper_runtime(
            args.session_id,
            operator=args.operator,
            note=args.note,
        )
        result = {
            "schema_version": "mil3.isolated-paper-runtime-command.v1",
            "execution_mode": "PAPER_ONLY",
            "action": "STOP",
            "session_id": args.session_id,
            "event_id": event_id,
            "already_stopped": event_id is None,
        }
    elif args.action in {"ARM_KILL", "CLEAR_KILL"}:
        if not args.operator or not args.note:
            parser.error("--operator and --note are required for kill-switch actions")
        event_id = store.set_isolated_paper_runtime_kill_switch(
            args.sandbox_id,
            action="ARM" if args.action == "ARM_KILL" else "CLEAR",
            operator=args.operator,
            note=args.note,
        )
        result = {
            "schema_version": "mil3.isolated-paper-runtime-command.v1",
            "execution_mode": "PAPER_ONLY",
            "action": args.action,
            "sandbox_id": args.sandbox_id,
            "event_id": event_id,
            "kill_switch": store.isolated_paper_runtime_kill_switch(args.sandbox_id),
        }
    else:
        result = store.reconcile_isolated_paper_runtime_sessions()
    result.update({
        "browser_control_allowed": False,
        "replay_started": False,
        "order_path_present": False,
        "shared_configuration_change_allowed": False,
        "automatic_strategy_change_allowed": False,
        "live_execution_allowed": False,
    })
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
