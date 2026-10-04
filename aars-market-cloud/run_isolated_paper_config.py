from __future__ import annotations

import argparse
import json
from pathlib import Path

from aars_market.isolated_config import (
    build_isolated_configuration,
    build_sandbox_event,
)
from aars_market.storage import MarketStore


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Govern the MIL-3.21 isolated PAPER_ONLY configuration registry"
    )
    parser.add_argument("--db", default="mil3_market.sqlite")
    parser.add_argument(
        "--action", required=True,
        choices=("REGISTER", "ACTIVATE", "ROLLBACK", "RECONCILE"),
    )
    parser.add_argument("--trial-id")
    parser.add_argument("--configuration-id")
    parser.add_argument("--sandbox-id", default="aars-paper-sandbox")
    parser.add_argument("--operator")
    parser.add_argument("--note")
    args = parser.parse_args()

    store = MarketStore(Path(args.db))
    store.init_db()
    if args.action == "REGISTER":
        if not args.trial_id:
            parser.error("--trial-id is required for REGISTER")
        payload = build_isolated_configuration(store, args.trial_id)
        configuration_id = store.archive_isolated_paper_configuration(payload)
        print("execution_mode=PAPER_ONLY")
        print(f"configuration_id={configuration_id} immutable=true")
        print(f"sandbox_id={payload['sandbox_id']}")
        print("registry_entry_inert=true")
    elif args.action in {"ACTIVATE", "ROLLBACK"}:
        if not args.operator or not args.note:
            parser.error("--operator and --note are required for ACTIVATE/ROLLBACK")
        if args.action == "ACTIVATE" and not args.configuration_id:
            parser.error("--configuration-id is required for ACTIVATE")
        event = build_sandbox_event(
            store,
            args.sandbox_id,
            action=args.action,
            configuration_id=args.configuration_id,
            operator=args.operator,
            note=args.note,
        )
        event_id = store.archive_isolated_paper_sandbox_event(event)
        print("execution_mode=PAPER_ONLY")
        print(f"event_id={event_id} immutable=true")
        print(f"action={args.action}")
        print(f"sandbox_id={args.sandbox_id}")
        print(f"stored_configuration_id={event['next_configuration_id'] or 'EMPTY'}")
    else:
        summary = store.reconcile_isolated_paper_sandboxes()
        print(json.dumps(summary, indent=2, sort_keys=True, allow_nan=False))
    print("starts_strategy_process=false")
    print("shared_configuration_change_allowed=false")
    print("automatic_strategy_change_allowed=false")
    print("live_execution_allowed=false")


if __name__ == "__main__":
    main()
