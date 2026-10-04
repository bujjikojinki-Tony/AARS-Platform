from __future__ import annotations

import argparse
from pathlib import Path

from aars_market.activation_approval import (
    build_isolated_activation_review,
    build_isolated_activation_revocation,
)
from aars_market.evidence_offline import (
    build_offline_verification_report,
    load_evidence_file,
)
from aars_market.storage import MarketStore


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Archive a MIL-3.20 isolated PAPER_ONLY activation review"
    )
    parser.add_argument("--db", default="mil3_market.sqlite")
    parser.add_argument("--trial-id", required=True)
    parser.add_argument(
        "--action",
        required=True,
        choices=(
            "APPROVE_ISOLATED_PAPER_ACTIVATION",
            "REJECT_ISOLATED_PAPER_ACTIVATION",
            "REVOKE_ISOLATED_PAPER_ACTIVATION",
        ),
    )
    parser.add_argument("--bundle")
    parser.add_argument("--reviewer", required=True)
    parser.add_argument("--note", required=True)
    parser.add_argument("--sandbox-id", default="aars-paper-sandbox")
    parser.add_argument("--validity-hours", type=int, default=24)
    args = parser.parse_args()

    store = MarketStore(Path(args.db))
    store.init_db()
    if args.action == "REVOKE_ISOLATED_PAPER_ACTIVATION":
        if args.bundle:
            parser.error("--bundle is not used for revocation")
        payload = build_isolated_activation_revocation(
            store,
            args.trial_id,
            reviewer=args.reviewer,
            note=args.note,
        )
    else:
        if not args.bundle:
            parser.error("--bundle is required for approve/reject")
        _, bundle = load_evidence_file(args.bundle)
        report = build_offline_verification_report(args.bundle)
        payload = build_isolated_activation_review(
            store,
            bundle,
            report,
            action=args.action,
            reviewer=args.reviewer,
            note=args.note,
            sandbox_id=args.sandbox_id,
            validity_hours=args.validity_hours,
        )
    review_id = store.archive_isolated_activation_review(payload)
    print("execution_mode=PAPER_ONLY")
    print(f"review_id={review_id} immutable=true")
    print(f"trial_id={args.trial_id}")
    print(f"resulting_state={payload['resulting_state']}")
    print(f"isolated_paper_activation_allowed={str(payload['authority']['isolated_paper_activation_allowed']).lower()}")
    print("approval_applies_configuration=false")
    print("shared_configuration_change_allowed=false")
    print("automatic_strategy_change_allowed=false")
    print("live_execution_allowed=false")


if __name__ == "__main__":
    main()
