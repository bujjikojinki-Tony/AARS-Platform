from __future__ import annotations

import argparse
import json
from pathlib import Path

from aars_market.challenger import build_low_turnover_challenger
from aars_market.storage import MarketStore


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Read-only MIL-3.28 low-turnover PAPER_ONLY challenger"
    )
    parser.add_argument("--db", default="mil3_market.sqlite")
    parser.add_argument("--snapshot-id")
    parser.add_argument("--output-json")
    args = parser.parse_args()

    database = Path(args.db)
    if not database.is_file():
        raise SystemExit(f"market database not found: {database}")
    payload = build_low_turnover_challenger(
        MarketStore(database), snapshot_id=args.snapshot_id
    )
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
    if payload["comparison"]:
        comparison = payload["comparison"]
        print(
            f"baseline_actual_return={comparison['baseline']['actual_cost']['total_return']:+.4%} "
            f"challenger_actual_return={comparison['challenger']['actual_cost']['total_return']:+.4%} "
            f"delta={comparison['deltas']['actual_return']:+.4%}"
        )
        print(
            f"turnover_reduction={comparison['deltas']['turnover_reduction']:.4%} "
            f"zero_cost_policy_delta={comparison['deltas']['zero_cost_policy_return']:+.4%} "
            f"disposition={payload['review_gate']['disposition']}"
        )
    else:
        print(f"reason={payload['data_trust']['reason']}")
    if args.output_json:
        print(f"challenger_report={Path(args.output_json).resolve()}")
    print("proposal_creation_allowed=false automatic_strategy_change_allowed=false")
    print("live_execution_allowed=false")


if __name__ == "__main__":
    main()
