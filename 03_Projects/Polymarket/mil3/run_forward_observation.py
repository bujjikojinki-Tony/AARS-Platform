from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from aars_market.forward import ForwardObservationSettings, build_forward_observation
from aars_market.storage import MarketStore


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Archive one MIL-3.17 forward-only PAPER_ONLY observation checkpoint"
    )
    parser.add_argument("--db", default="mil3_market.sqlite")
    parser.add_argument("--trial-id", required=True)
    parser.add_argument("--as-of", help="optional ISO-8601 synchronized market boundary")
    parser.add_argument("--minimum-forward-bars", type=int, default=24)
    parser.add_argument("--confirmation-bars", type=int, default=168)
    args = parser.parse_args()

    store = MarketStore(Path(args.db))
    store.init_db()
    trial = store.get_paper_trial_result(args.trial_id)
    if trial is None:
        raise SystemExit(f"paper trial not found: {args.trial_id}")
    payload = build_forward_observation(
        store,
        trial,
        settings=ForwardObservationSettings(
            minimum_forward_bars=args.minimum_forward_bars,
            confirmation_bars=args.confirmation_bars,
        ),
        as_of=datetime.fromisoformat(args.as_of) if args.as_of else None,
    )
    observation_id = store.archive_forward_observation(payload)
    print("execution_mode=PAPER_ONLY")
    print(f"observation_id={observation_id} immutable=true forward_only=true")
    print(f"trial_id={args.trial_id}")
    print(f"observed_through={payload['boundary']['synchronized_forward_end']}")
    print(f"forward_bars={payload['results']['forward_bars']}")
    print(f"disposition={payload['review_gate']['disposition']}")
    print("observation_application_allowed=false")
    print("automatic_strategy_change_allowed=false")
    print("live_execution_allowed=false")


if __name__ == "__main__":
    main()
