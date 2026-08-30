from __future__ import annotations

import argparse
from pathlib import Path

from aars_market.replay import summarize_replay, walk_forward_replay
from aars_market.storage import MarketStore


def main() -> None:
    parser = argparse.ArgumentParser(description="AARS MIL-3.1 walk-forward replay")
    parser.add_argument("--db", default="mil3_market.sqlite")
    parser.add_argument("--symbol", default="SOLUSDT")
    parser.add_argument("--interval", default="1h")
    parser.add_argument("--horizon", type=int, default=24)
    parser.add_argument("--warmup", type=int, default=120)
    parser.add_argument("--threshold", type=float, default=0.02)
    args = parser.parse_args()

    store = MarketStore(Path(args.db))
    store.init_db()
    candles = store.load_candles(args.symbol, args.interval)
    records = walk_forward_replay(
        candles,
        horizon_bars=args.horizon,
        warmup_bars=args.warmup,
        outcome_threshold=args.threshold,
    )
    summary = summarize_replay(records)

    print("execution_mode=PAPER_ONLY")
    print(f"symbol={args.symbol.upper()} interval={args.interval} candles={len(candles)}")
    print(
        "replay_records={records} bull_rate={bull:.3f} base_rate={base:.3f} "
        "bear_rate={bear:.3f} mean_brier={brier:.4f} mean_forward_return={ret:.4%}".format(
            records=summary.records,
            bull=summary.bull_rate,
            base=summary.base_rate,
            bear=summary.bear_rate,
            brier=summary.mean_brier_score,
            ret=summary.mean_forward_return,
        )
    )

    by_state: dict[str, list[float]] = {}
    for record in records:
        by_state.setdefault(record.state.value, []).append(record.forward_return)
    for state, returns in sorted(by_state.items()):
        mean_return = sum(returns) / len(returns)
        print(f"state={state:16s} n={len(returns):4d} mean_forward_return={mean_return:.4%}")


if __name__ == "__main__":
    main()
