from __future__ import annotations

import argparse
from pathlib import Path

from aars_market.evidence_export import (
    build_forward_evidence_bundle,
    verify_forward_evidence_bundle,
    write_forward_evidence_bundle,
)
from aars_market.storage import MarketStore


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export one self-verifying MIL-3.19 PAPER_ONLY evidence bundle"
    )
    parser.add_argument("--db", default="mil3_market.sqlite")
    parser.add_argument("--trial-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    store = MarketStore(Path(args.db))
    store.init_db()
    bundle = build_forward_evidence_bundle(store, args.trial_id)
    output = write_forward_evidence_bundle(bundle, args.output)
    print("execution_mode=PAPER_ONLY")
    print(f"evidence_bundle={output}")
    print(f"combined_sha256={bundle['manifest']['combined_sha256']}")
    print(f"verified={str(verify_forward_evidence_bundle(bundle)).lower()}")
    print("evidence_export_only=true")
    print("automatic_strategy_change_allowed=false")
    print("live_execution_allowed=false")


if __name__ == "__main__":
    main()
