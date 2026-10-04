from __future__ import annotations

import argparse
from pathlib import Path

from aars_market.storage import MarketStore
from aars_market.trial import PaperTrialSettings, build_paper_trial_result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run and archive one isolated MIL-3.16 PAPER_ONLY proposal trial"
    )
    parser.add_argument("--db", default="mil3_market.sqlite")
    parser.add_argument("--proposal-id", required=True)
    parser.add_argument("--initial-equity-per-asset", type=float, default=1000.0)
    parser.add_argument("--fee-rate", type=float, default=0.0005)
    parser.add_argument("--slippage-rate", type=float, default=0.0002)
    parser.add_argument("--maintenance-margin-rate", type=float, default=0.005)
    parser.add_argument("--stop-max-drawdown", type=float, default=0.20)
    parser.add_argument("--stop-max-liquidation-risk", type=float, default=0.10)
    args = parser.parse_args()

    store = MarketStore(Path(args.db))
    store.init_db()
    envelope = store.get_paper_configuration_proposal(args.proposal_id)
    if envelope is None:
        raise SystemExit(f"paper proposal not found: {args.proposal_id}")
    result = build_paper_trial_result(
        store,
        envelope,
        settings=PaperTrialSettings(
            initial_equity_per_asset=args.initial_equity_per_asset,
            fee_rate=args.fee_rate,
            slippage_rate=args.slippage_rate,
            maintenance_margin_rate=args.maintenance_margin_rate,
            stop_max_drawdown=args.stop_max_drawdown,
            stop_max_liquidation_risk=args.stop_max_liquidation_risk,
        ),
    )
    trial_id = store.archive_paper_trial_result(result)
    print("execution_mode=PAPER_ONLY")
    print(f"trial_id={trial_id} immutable=true")
    print(f"proposal_id={args.proposal_id}")
    print(f"disposition={result['review_gate']['disposition']}")
    print(f"stop_triggered={str(result['stop_condition']['triggered']).lower()}")
    print("trial_application_allowed=false")
    print("automatic_strategy_change_allowed=false")
    print("live_execution_allowed=false")


if __name__ == "__main__":
    main()
