from __future__ import annotations

import argparse
from pathlib import Path

from aars_market.simulation import simulate_aars_dynamic, simulate_buy_hold
from aars_market.storage import MarketStore


def _print(summary) -> None:
    print(
        f"{summary.strategy:12s} return={summary.total_return:+.2%} "
        f"max_dd={summary.max_drawdown:.2%} sharpe≈{summary.sharpe_approx:.2f} "
        f"fees={summary.fees:.2f} turnover={summary.turnover_notional:.2f} "
        f"final_exposure={summary.final_net_exposure:+.2f}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="AARS MIL-3 paper comparison")
    parser.add_argument("--db", default="mil3_market.sqlite")
    parser.add_argument("--symbol", default="SOLUSDT")
    parser.add_argument("--interval", default="1h")
    parser.add_argument("--initial-equity", type=float, default=1000.0)
    parser.add_argument("--warmup", type=int, default=120)
    parser.add_argument("--max-exposure", type=float, default=1.0)
    args = parser.parse_args()

    store = MarketStore(Path(args.db))
    store.init_db()
    candles = store.load_candles(args.symbol, args.interval)
    if len(candles) <= args.warmup:
        raise SystemExit(f"need > {args.warmup} candles; stored={len(candles)}")

    print("execution_mode=PAPER_ONLY")
    print(f"symbol={args.symbol.upper()} interval={args.interval} candles={len(candles)}")
    buy_hold = simulate_buy_hold(
        candles,
        initial_equity=args.initial_equity,
        warmup_bars=args.warmup,
    )
    aars = simulate_aars_dynamic(
        candles,
        initial_equity=args.initial_equity,
        warmup_bars=args.warmup,
        max_abs_exposure=args.max_exposure,
    )
    _print(buy_hold)
    _print(aars)

    if aars.max_drawdown < buy_hold.max_drawdown:
        print("risk_result=AARS_LOWER_DRAWDOWN")
    else:
        print("risk_result=AARS_NOT_LOWER_DRAWDOWN")
    if aars.sharpe_approx > buy_hold.sharpe_approx:
        print("risk_adjusted_result=AARS_BETTER")
    else:
        print("risk_adjusted_result=AARS_NOT_BETTER")


if __name__ == "__main__":
    main()
