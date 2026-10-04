from __future__ import annotations

import argparse
from pathlib import Path

from aars_market.storage import MarketStore
from aars_market.validation import (
    ValidationSettings,
    build_candidates,
    combine_validation_reports,
    walk_forward_validate,
    write_validation_report,
)


def _floats(value: str) -> list[float]:
    return [float(item) for item in value.split(",") if item.strip()]


def _ints(value: str) -> list[int]:
    return [int(item) for item in value.split(",") if item.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="AARS MIL-3.11 walk-forward robustness validation")
    parser.add_argument("--db", default="mil3_market.sqlite")
    parser.add_argument("--symbol", default="SOLUSDT")
    parser.add_argument(
        "--symbols",
        nargs="+",
        help="validate several assets into one comparable batch report",
    )
    parser.add_argument("--interval", default="1h")
    parser.add_argument(
        "--strategy",
        choices=("AARS_DYNAMIC", "SPOT_GRID", "FUTURES_LONG_GRID"),
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
    parser.add_argument("--output-json", required=True)
    args = parser.parse_args()

    store = MarketStore(Path(args.db))
    store.init_db()
    hedge_modes = {
        "both": (True, False),
        "on": (True,),
        "off": (False,),
    }[args.hedge_modes]
    candidates = build_candidates(
        args.strategy,
        aars_exposures=args.aars_exposures,
        futures_leverages=args.futures_leverages,
        grid_spacings=args.grid_spacings,
        grid_levels=args.grid_levels,
        tactical_hedges=hedge_modes,
        candidate_cap=args.candidate_cap,
    )
    symbols = tuple(dict.fromkeys(item.upper() for item in (args.symbols or [args.symbol])))
    reports = []
    for symbol in symbols:
        candles = store.load_candles(symbol, args.interval)
        if not candles:
            raise SystemExit(f"no candles stored for {symbol} {args.interval}")
        funding = store.load_funding_rates(
            symbol, candles[0].open_time, candles[-1].open_time
        )
        reports.append(
            walk_forward_validate(
                candles,
                candidates,
                train_bars=args.train_bars,
                test_bars=args.test_bars,
                step_bars=args.step_bars,
                settings=ValidationSettings(
                    warmup_bars=args.warmup,
                    initial_equity=args.initial_equity,
                    fee_rate=args.fee_rate,
                    slippage_rate=args.slippage_rate,
                    funding_rate_per_bar=args.funding_rate_per_bar,
                    funding_rates=tuple(funding),
                    maintenance_margin_rate=args.maintenance_margin_rate,
                ),
            )
        )
    payload = reports[0] if len(reports) == 1 else combine_validation_reports(reports)
    write_validation_report(args.output_json, payload)
    aggregate = payload["aggregate"]
    print("execution_mode=PAPER_ONLY")
    if len(reports) == 1:
        print(f"target_strategy={payload['target_strategy']} candidates={len(candidates)} folds={aggregate['folds']}")
        print(
            f"mean_test_return={aggregate['mean_test_return']:+.2%} "
            f"mean_buy_hold_return={aggregate['mean_buy_hold_return']:+.2%} "
            f"beat_buy_hold_folds={aggregate['beat_buy_hold_folds']}/{aggregate['folds']} "
            f"selection_stability={aggregate['selection_stability']:.2%}"
        )
    else:
        print(
            f"target_strategy={payload['target_strategy']} candidates={len(candidates)} "
            f"assets={aggregate['assets']} total_folds={aggregate['total_folds']}"
        )
        print(
            f"mean_asset_test_return={aggregate['mean_asset_test_return']:+.2%} "
            f"mean_asset_buy_hold_return={aggregate['mean_asset_buy_hold_return']:+.2%} "
            f"beat_buy_hold_ratio={aggregate['beat_buy_hold_ratio']:.2%}"
        )
    print(f"review_gate={payload['review_gate']['disposition']}")
    print(f"validation_report={Path(args.output_json).resolve()}")


if __name__ == "__main__":
    main()
