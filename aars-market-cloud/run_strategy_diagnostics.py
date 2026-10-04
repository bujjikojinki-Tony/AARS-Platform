from __future__ import annotations

import argparse
import json
from pathlib import Path

from aars_market.diagnostics import build_strategy_diagnostics
from aars_market.storage import MarketStore


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Read-only MIL-3.27 strategy diagnostic over immutable v2 evidence"
    )
    parser.add_argument("--db", default="mil3_market.sqlite")
    parser.add_argument("--snapshot-id")
    parser.add_argument("--output-json")
    args = parser.parse_args()

    database = Path(args.db)
    if not database.is_file():
        raise SystemExit(f"market database not found: {database}")
    store = MarketStore(database)
    payload = build_strategy_diagnostics(store, snapshot_id=args.snapshot_id)
    if args.output_json:
        output = Path(args.output_json)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
            encoding="utf-8",
        )
    print("execution_mode=PAPER_ONLY read_only=true")
    print(
        f"status={payload['status']} data_trust={payload['data_trust']['status']} "
        f"snapshot_id={payload['data_trust'].get('source_snapshot_id')}"
    )
    if payload["attribution"]:
        attribution = payload["attribution"]
        print(
            f"aars_return={attribution['aars_total_return']:+.4%} "
            f"buy_hold_return={attribution['buy_hold_total_return']:+.4%} "
            f"gap={attribution['return_gap_vs_buy_hold']:+.4%}"
        )
        print(
            f"cost_drag={attribution['weighted_cost_drag_return']:.4%} "
            f"largest_cost={attribution['largest_cost_component']} "
            f"highest_asset_drag={attribution['highest_asset_drag']}"
        )
    else:
        print(f"reason={payload['data_trust']['reason']}")
    if args.output_json:
        print(f"diagnostic_report={Path(args.output_json).resolve()}")
    print("automatic_strategy_change_allowed=false live_execution_allowed=false")


if __name__ == "__main__":
    main()
