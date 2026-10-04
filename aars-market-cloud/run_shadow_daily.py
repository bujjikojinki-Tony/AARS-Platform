from __future__ import annotations

import argparse
from pathlib import Path

from aars_market.shadow import build_shadow_daily_snapshot
from aars_market.storage import MarketStore
from aars_market.validation import ValidationSettings, build_candidates


def _floats(value: str) -> list[float]:
    return [float(item) for item in value.split(",") if item.strip()]


def _ints(value: str) -> list[int]:
    return [int(item) for item in value.split(",") if item.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Archive one explicit AARS MIL-3.12 PAPER_ONLY daily shadow cycle"
    )
    parser.add_argument("--db", default="mil3_market.sqlite")
    parser.add_argument("--symbols", nargs="+", default=["BTCUSDT", "ETHUSDT", "SOLUSDT"])
    parser.add_argument("--interval", default="1h")
    parser.add_argument("--window", choices=("30d", "90d", "180d", "365d", "all"), default="90d")
    parser.add_argument(
        "--validation-strategy",
        choices=("AARS_DYNAMIC", "SPOT_GRID", "FUTURES_LONG_GRID"),
        default="AARS_DYNAMIC",
    )
    parser.add_argument(
        "--portfolio-strategy",
        choices=("BUY_HOLD", "SPOT_GRID", "FUTURES_LONG_GRID", "AARS_DYNAMIC"),
        default="AARS_DYNAMIC",
    )
    parser.add_argument("--warmup", type=int, default=120)
    parser.add_argument("--train-bars", type=int, default=720)
    parser.add_argument("--test-bars", type=int, default=168)
    parser.add_argument("--step-bars", type=int)
    parser.add_argument("--aars-exposures", type=_floats, default=_floats("0.25,0.5,0.75,1"))
    parser.add_argument("--futures-leverages", type=_floats, default=_floats("2,5,10"))
    parser.add_argument("--grid-spacings", type=_floats, default=_floats("0.005,0.01,0.02"))
    parser.add_argument("--grid-levels", type=_ints, default=_ints("3,5"))
    parser.add_argument("--hedge-modes", choices=("both", "on", "off"), default="both")
    parser.add_argument("--candidate-cap", type=int, default=64)
    parser.add_argument("--initial-equity", type=float, default=1000.0)
    parser.add_argument("--fee-rate", type=float, default=0.0005)
    parser.add_argument("--slippage-rate", type=float, default=0.0002)
    parser.add_argument("--funding-rate-per-bar", type=float, default=0.0)
    parser.add_argument("--maintenance-margin-rate", type=float, default=0.005)
    args = parser.parse_args()

    store = MarketStore(Path(args.db))
    store.init_db()
    hedge_modes = {"both": (True, False), "on": (True,), "off": (False,)}[
        args.hedge_modes
    ]
    candidates = build_candidates(
        args.validation_strategy,
        aars_exposures=args.aars_exposures,
        futures_leverages=args.futures_leverages,
        grid_spacings=args.grid_spacings,
        grid_levels=args.grid_levels,
        tactical_hedges=hedge_modes,
        candidate_cap=args.candidate_cap,
    )
    payload = build_shadow_daily_snapshot(
        store,
        candidates,
        symbols=args.symbols,
        timeframe=args.interval,
        replay_window=args.window,
        portfolio_strategy=args.portfolio_strategy,
        train_bars=args.train_bars,
        test_bars=args.test_bars,
        step_bars=args.step_bars,
        settings=ValidationSettings(
            warmup_bars=args.warmup,
            initial_equity=args.initial_equity,
            fee_rate=args.fee_rate,
            slippage_rate=args.slippage_rate,
            funding_rate_per_bar=args.funding_rate_per_bar,
            maintenance_margin_rate=args.maintenance_margin_rate,
        ),
    )
    snapshot_id = store.archive_shadow_daily_snapshot(payload)
    print("execution_mode=PAPER_ONLY")
    print(f"snapshot_id={snapshot_id} immutable=true")
    print(f"as_of={payload['as_of']}")
    print(f"observation_date={payload['observation_date']}")
    print(
        "closed_candle_boundary="
        f"{payload['evidence_boundary']['fully_closed']}"
    )
    print(f"review_gate={payload['review_gate']['disposition']}")
    print(f"snapshots_stored={len(store.list_shadow_daily_snapshots(limit=1000000))}")


if __name__ == "__main__":
    main()
