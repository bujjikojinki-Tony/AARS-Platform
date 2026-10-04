from __future__ import annotations

import argparse
import json
from pathlib import Path

from aars_market.robustness import build_frozen_challenger_robustness
from aars_market.storage import MarketStore


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Read-only MIL-3.29 frozen PAPER_ONLY robustness validation"
    )
    parser.add_argument("--db", default="mil3_market.sqlite")
    parser.add_argument("--snapshot-id")
    parser.add_argument("--output-json")
    args = parser.parse_args()

    database = Path(args.db)
    if not database.is_file():
        raise SystemExit(f"market database not found: {database}")
    payload = build_frozen_challenger_robustness(
        MarketStore(database), snapshot_id=args.snapshot_id
    )
    if args.output_json:
        output = Path(args.output_json)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
            encoding="utf-8",
        )
    print("execution_mode=PAPER_ONLY read_only=true parameter_tuning_allowed=false")
    print(
        f"status={payload['status']} data_trust={payload['data_trust']['status']} "
        f"snapshot_id={payload['data_trust'].get('source_snapshot_id')}"
    )
    if payload["frozen_specification"]:
        print(
            f"spec_sha256={payload['frozen_specification']['spec_sha256']} "
            f"disposition={payload['review_gate']['disposition']} "
            f"overfit={payload['overfit_assessment']['level']}"
        )
        print(
            f"windows={len(payload['multi_window'])} "
            f"folds={payload['walk_forward']['fold_count']} "
            f"post_freeze_folds={payload['overfit_assessment']['post_freeze_folds']}"
        )
    else:
        print(f"reason={payload['data_trust']['reason']}")
    if args.output_json:
        print(f"robustness_report={Path(args.output_json).resolve()}")
    print("proposal_creation_allowed=false challenger_activation_allowed=false")
    print("live_execution_allowed=false")


if __name__ == "__main__":
    main()
