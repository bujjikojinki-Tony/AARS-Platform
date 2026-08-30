from __future__ import annotations

import argparse
import json
from pathlib import Path

from aars_market.frozen_monitor import (
    build_frozen_forward_evidence_view,
    run_frozen_evidence_cycle,
    run_frozen_evidence_scheduler,
)
from aars_market.storage import MarketStore


def _print_view(payload: dict) -> None:
    print(
        f"status={payload['status']} data_trust={payload['data_trust']['status']} "
        f"snapshot_id={payload['data_trust'].get('source_snapshot_id')}"
    )
    if payload["collection"]:
        collection = payload["collection"]
        print(
            f"checkpoints={collection['checkpoint_count']} "
            f"post_freeze_folds={collection['latest_archived_post_freeze_fold_count']}/"
            f"{collection['minimum_required_post_freeze_folds']} "
            f"available={collection['available_post_freeze_fold_count']} "
            f"next_eligible_after={collection['next_eligible_after']}"
        )
        print(
            f"drift={payload['drift']['status']} "
            f"highest_severity={payload['drift']['highest_severity']} "
            f"disposition={payload['review_gate']['disposition']}"
        )
    else:
        print(f"reason={payload['data_trust']['reason']}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="MIL-3.30 frozen PAPER_ONLY weekly evidence monitor"
    )
    parser.add_argument("--db", default="mil3_market.sqlite")
    parser.add_argument("--snapshot-id")
    parser.add_argument(
        "--action", choices=("STATUS", "WAKE", "FOREGROUND"), default="STATUS"
    )
    parser.add_argument("--poll-seconds", type=float, default=3600.0)
    parser.add_argument(
        "--max-cycles", type=int, default=1,
        help="FOREGROUND cycles; 0 runs until interrupted",
    )
    parser.add_argument("--output-json")
    args = parser.parse_args()

    store = MarketStore(Path(args.db))
    store.init_db()
    print("execution_mode=PAPER_ONLY")
    print("monitor_scope=FROZEN_WEEKLY_EVIDENCE_ONLY")
    print("parameter_tuning_allowed=false proposal_creation_allowed=false")
    print("challenger_activation_allowed=false live_execution_allowed=false")
    payload: dict | None = None
    try:
        if args.action == "STATUS":
            payload = build_frozen_forward_evidence_view(
                store, snapshot_id=args.snapshot_id
            )
            _print_view(payload)
        elif args.action == "WAKE":
            cycle = run_frozen_evidence_cycle(
                store, snapshot_id=args.snapshot_id
            )
            print(
                f"cycle_status={cycle['status']} "
                f"archived={len(cycle['archived'])}"
            )
            payload = cycle["view"]
            _print_view(payload)
        else:
            summaries = run_frozen_evidence_scheduler(
                store,
                interval_seconds=args.poll_seconds,
                max_cycles=args.max_cycles or None,
                snapshot_id=args.snapshot_id,
                on_cycle=lambda cycle: print(
                    json.dumps(
                        {
                            "status": cycle["status"],
                            "archived": len(cycle["archived"]),
                            "evaluated_at": cycle.get("evaluated_at"),
                            "disposition": cycle["view"]["review_gate"]["disposition"],
                        },
                        sort_keys=True,
                    )
                ),
            )
            payload = summaries[-1]["view"] if summaries else None
    except KeyboardInterrupt:
        print("monitor_status=STOPPED_BY_USER")
    if args.output_json and payload is not None:
        output = Path(args.output_json)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        print(f"monitor_report={output.resolve()}")


if __name__ == "__main__":
    main()
