from __future__ import annotations

import argparse
from pathlib import Path

from aars_market.governance import build_promotion_governance
from aars_market.proposal import build_paper_configuration_proposal
from aars_market.shadow import build_shadow_stability
from aars_market.storage import MarketStore


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Archive one advisory MIL-3.15 PAPER_ONLY configuration proposal"
    )
    parser.add_argument("--db", default="mil3_market.sqlite")
    parser.add_argument(
        "--strategy",
        choices=("AARS_DYNAMIC", "SPOT_GRID", "FUTURES_LONG_GRID"),
        default="AARS_DYNAMIC",
    )
    parser.add_argument("--history-limit", type=int, default=90)
    args = parser.parse_args()

    store = MarketStore(Path(args.db))
    store.init_db()
    snapshots = store.load_shadow_daily_snapshots(
        limit=args.history_limit, target_strategy=args.strategy
    )
    if not snapshots:
        raise SystemExit("no immutable shadow snapshots available for proposal evidence")
    stability = build_shadow_stability(snapshots)
    governance = build_promotion_governance(stability)
    snapshot_id, snapshot = snapshots[-1]
    proposal = build_paper_configuration_proposal(
        governance, snapshot_id, snapshot
    )
    proposal_id = store.archive_paper_configuration_proposal(proposal)
    print("execution_mode=PAPER_ONLY")
    print(f"proposal_id={proposal_id} immutable=true")
    print("status=PENDING_HUMAN_REVIEW")
    print("proposal_application_allowed=false")
    print("automatic_strategy_change_allowed=false")
    print("live_execution_allowed=false")


if __name__ == "__main__":
    main()
