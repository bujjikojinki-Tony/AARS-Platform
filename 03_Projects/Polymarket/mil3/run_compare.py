from __future__ import annotations

import argparse
from pathlib import Path

from aars_market.simulation import SimulationSummary, compare_shadow_strategies
from aars_market.storage import MarketStore


def _print(summary: SimulationSummary) -> None:
    profit_factor = "inf" if summary.profit_factor == float("inf") else f"{summary.profit_factor:.2f}"
    print(
        f"{summary.strategy:23s} "
        f"return={summary.total_return:+.2%} max_dd={summary.max_drawdown:.2%} "
        f"sharpe={summary.sharpe_approx:+.2f} sortino={summary.sortino:+.2f} "
        f"profit_factor={profit_factor} turnover={summary.turnover_notional:.2f} "
        f"fees={summary.fees:.2f} slippage={summary.slippage:.2f} funding={summary.funding:+.2f} "
        f"grid_realized={summary.realized_grid_pnl:+.2f} inventory_unrealized={summary.inventory_unrealized_pnl:+.2f} "
        f"net_exposure={summary.final_net_exposure:+.2f} max_leverage={summary.max_effective_leverage:.2f}x "
        f"min_margin_buffer={summary.min_margin_buffer_pct:.2%} "
        f"liquidation_risk={summary.max_liquidation_risk:.2%} liquidation_events={summary.liquidation_events}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="AARS MIL-3 paper comparison")
    parser.add_argument("--db", default="mil3_market.sqlite")
    parser.add_argument("--symbol", default="SOLUSDT")
    parser.add_argument("--interval", default="1h")
    parser.add_argument("--initial-equity", type=float, default=1000.0)
    parser.add_argument("--warmup", type=int, default=120)
    parser.add_argument(
        "--aars-max-exposure",
        "--max-exposure",
        dest="aars_max_exposure",
        type=float,
        default=1.0,
        help="AARS signed exposure cap; --max-exposure remains as a compatibility alias",
    )
    parser.add_argument("--futures-leverage", type=float, default=10.0)
    parser.add_argument("--grid-spacing", type=float, default=0.01)
    parser.add_argument("--grid-levels", type=int, default=5)
    parser.add_argument("--fee-rate", type=float, default=0.0005)
    parser.add_argument("--slippage-rate", type=float, default=0.0002)
    parser.add_argument("--funding-rate-per-bar", type=float, default=0.0)
    parser.add_argument("--maintenance-margin-rate", type=float, default=0.005)
    parser.add_argument("--no-tactical-hedge", action="store_true")
    args = parser.parse_args()

    store = MarketStore(Path(args.db))
    store.init_db()
    candles = store.load_candles(args.symbol, args.interval)
    if len(candles) <= args.warmup:
        raise SystemExit(f"need > {args.warmup} candles; stored={len(candles)}")

    print("execution_mode=PAPER_ONLY")
    print(f"symbol={args.symbol.upper()} interval={args.interval} candles={len(candles)}")
    summaries = compare_shadow_strategies(
        candles,
        initial_equity=args.initial_equity,
        warmup_bars=args.warmup,
        futures_leverage=args.futures_leverage,
        aars_max_abs_exposure=args.aars_max_exposure,
        grid_spacing_pct=args.grid_spacing,
        grid_levels=args.grid_levels,
        tactical_hedge=not args.no_tactical_hedge,
        fee_rate=args.fee_rate,
        slippage_rate=args.slippage_rate,
        funding_rate_per_bar=args.funding_rate_per_bar,
        maintenance_margin_rate=args.maintenance_margin_rate,
    )
    for summary in summaries:
        _print(summary)

    buy_hold, _, futures_grid, aars = summaries
    if aars.max_drawdown < buy_hold.max_drawdown:
        print("risk_result=AARS_LOWER_DRAWDOWN")
    else:
        print("risk_result=AARS_NOT_LOWER_DRAWDOWN")
    if aars.sharpe_approx > buy_hold.sharpe_approx:
        print("risk_adjusted_result=AARS_BETTER")
    else:
        print("risk_adjusted_result=AARS_NOT_BETTER")
    if futures_grid.liquidation_events:
        print("futures_risk_result=LIQUIDATION_APPROXIMATION_BREACHED")
    else:
        print("futures_risk_result=NO_APPROXIMATED_LIQUIDATION_BREACH")


if __name__ == "__main__":
    main()
