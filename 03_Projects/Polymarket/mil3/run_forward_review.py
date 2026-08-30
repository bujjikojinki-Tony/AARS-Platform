from __future__ import annotations

import argparse
from pathlib import Path

from aars_market.forward_review import build_forward_candidate_review
from aars_market.service import DashboardService
from aars_market.storage import MarketStore


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Archive one MIL-3.19 human PAPER_ONLY forward lifecycle review"
    )
    parser.add_argument("--db", default="mil3_market.sqlite")
    parser.add_argument("--trial-id", required=True)
    parser.add_argument(
        "--action",
        required=True,
        choices=(
            "ACKNOWLEDGE_FOR_PAPER_CONTINUATION",
            "PAUSE_PAPER_OBSERVATION",
            "TERMINATE_PAPER_OBSERVATION",
            "RESTART_PAPER_OBSERVATION",
        ),
    )
    parser.add_argument("--reviewer", required=True)
    parser.add_argument("--note", required=True)
    args = parser.parse_args()

    store = MarketStore(Path(args.db))
    store.init_db()
    stability = DashboardService(store).forward_stability(args.trial_id, limit=90)
    review = build_forward_candidate_review(
        store,
        args.trial_id,
        stability,
        action=args.action,
        reviewer=args.reviewer,
        note=args.note,
    )
    review_id = store.archive_forward_candidate_review(review)
    print("execution_mode=PAPER_ONLY")
    print(f"review_id={review_id} immutable=true")
    print(f"trial_id={args.trial_id}")
    print(f"action={review['action']}")
    print(f"resulting_state={review['resulting_state']}")
    print("review_action_applies_parameters=false")
    print("automatic_strategy_change_allowed=false")
    print("live_execution_allowed=false")


if __name__ == "__main__":
    main()
