from __future__ import annotations

import argparse
from pathlib import Path

from aars_market.proposal import build_paper_proposal_review
from aars_market.storage import MarketStore


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Archive one terminal human review of a MIL-3.15 PAPER_ONLY proposal"
    )
    parser.add_argument("--db", default="mil3_market.sqlite")
    parser.add_argument("--proposal-id", required=True)
    parser.add_argument(
        "--disposition",
        required=True,
        choices=("ACKNOWLEDGED_FOR_PAPER_TRIAL", "DECLINED"),
    )
    parser.add_argument("--reviewer", required=True)
    parser.add_argument("--note", required=True)
    args = parser.parse_args()

    store = MarketStore(Path(args.db))
    store.init_db()
    envelope = store.get_paper_configuration_proposal(args.proposal_id)
    if envelope is None:
        raise SystemExit(f"paper proposal not found: {args.proposal_id}")
    review = build_paper_proposal_review(
        args.proposal_id,
        envelope["proposal"],
        disposition=args.disposition,
        reviewer=args.reviewer,
        note=args.note,
    )
    review_id = store.archive_paper_proposal_review(review)
    print("execution_mode=PAPER_ONLY")
    print(f"review_id={review_id} immutable=true")
    print(f"proposal_id={args.proposal_id}")
    print(f"disposition={args.disposition}")
    print("acknowledgement_applies_parameters=false")
    print("automatic_strategy_change_allowed=false")
    print("live_execution_allowed=false")


if __name__ == "__main__":
    main()
