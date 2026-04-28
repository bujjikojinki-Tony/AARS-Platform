from __future__ import annotations

from collections import Counter, defaultdict

from weather_comparison_engine.schemas.training_sample import TrainingSample
from weather_comparison_engine.validation.quality_reports import (
    build_family_rollout_summary,
    build_family_rollout_trend_summary,
    build_family_rollout_watchlist,
    build_governance_summary,
)


class Backtester:
    def run(
        self,
        samples: list[TrainingSample],
        *,
        edge_threshold: float = 0.05,
    ) -> dict:
        labeled = [
            sample
            for sample in samples
            if sample.outcome in {"YES", "NO"}
            and _sample_probability(sample, "model_probability") is not None
            and _sample_probability(sample, "market_probability") is not None
        ]

        trades: list[dict] = []
        cumulative_pnl = 0.0
        equity_curve: list[float] = []

        for sample in labeled:
            edge = float(_sample_probability(sample, "model_probability")) - float(
                _sample_probability(sample, "market_probability")
            )
            if edge >= edge_threshold:
                trade = _trade_yes(sample, edge)
            elif edge <= -edge_threshold:
                trade = _trade_no(sample, edge)
            else:
                continue

            if trade is None:
                continue

            cumulative_pnl += trade["pnl"]
            equity_curve.append(cumulative_pnl)
            trade["cumulative_pnl"] = round(cumulative_pnl, 6)
            trades.append(trade)

        total_staked = len(trades)
        total_pnl = sum(trade["pnl"] for trade in trades)
        wins = sum(1 for trade in trades if trade["pnl"] > 0)
        hit_rate = (wins / len(trades)) if trades else None
        avg_edge_captured = (
            sum(abs(trade["edge"]) for trade in trades) / len(trades) if trades else None
        )
        max_drawdown = _max_drawdown(equity_curve) if equity_curve else None
        family_breakdown = _family_breakdown(trades)

        return {
            "sample_count": len(labeled),
            "trade_count": len(trades),
            "edge_threshold": edge_threshold,
            "total_pnl": round(total_pnl, 6),
            "roi": round(total_pnl / total_staked, 6) if total_staked else None,
            "max_drawdown": round(max_drawdown, 6) if max_drawdown is not None else None,
            "hit_rate": round(hit_rate, 6) if hit_rate is not None else None,
            "avg_edge_captured": round(avg_edge_captured, 6) if avg_edge_captured is not None else None,
            "turnover": len(trades),
            "position_counts": dict(Counter(trade["side"] for trade in trades)),
            "family_breakdown": family_breakdown,
            "governance_summary": build_governance_summary(samples),
            "family_rollout_summary": build_family_rollout_summary(samples),
            "family_rollout_trend_summary": build_family_rollout_trend_summary(samples),
            "family_rollout_watchlist": build_family_rollout_watchlist(samples),
            "note": (
                "Heuristic backtest uses model_probability vs market_probability edge with unit stake sizing. "
                "This is a validation scaffold, not a production execution model."
            ),
        }


def _trade_yes(sample: TrainingSample, edge: float) -> dict | None:
    entry_price = _entry_price(sample.yes_price, _sample_probability(sample, "market_probability"))
    if entry_price is None:
        return None
    pnl = (1 - entry_price) if sample.outcome == "YES" else -entry_price
    return {
        "market_id": sample.market_id,
        "market_family": sample.market_family or "unknown",
        "side": "YES",
        "edge": edge,
        "entry_price": entry_price,
        "pnl": pnl,
    }


def _trade_no(sample: TrainingSample, edge: float) -> dict | None:
    market_probability = _sample_probability(sample, "market_probability")
    fallback_no_price = (1 - market_probability) if market_probability is not None else None
    entry_price = _entry_price(sample.no_price, fallback_no_price)
    if entry_price is None:
        return None
    pnl = (1 - entry_price) if sample.outcome == "NO" else -entry_price
    return {
        "market_id": sample.market_id,
        "market_family": sample.market_family or "unknown",
        "side": "NO",
        "edge": edge,
        "entry_price": entry_price,
        "pnl": pnl,
    }


def _sample_probability(sample: TrainingSample, field: str) -> float | None:
    value = getattr(sample, field, None)
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _entry_price(primary: float | None, fallback: float | None) -> float | None:
    value = primary if primary is not None else fallback
    if value is None:
        return None
    return float(value)


def _max_drawdown(equity_curve: list[float]) -> float:
    peak = equity_curve[0] if equity_curve else 0.0
    max_drawdown = 0.0
    for equity in equity_curve:
        peak = max(peak, equity)
        max_drawdown = max(max_drawdown, peak - equity)
    return max_drawdown


def _family_breakdown(trades: list[dict]) -> dict[str, dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for trade in trades:
        grouped[trade["market_family"]].append(trade)

    result: dict[str, dict] = {}
    for family, family_trades in grouped.items():
        wins = sum(1 for trade in family_trades if trade["pnl"] > 0)
        result[family] = {
            "trade_count": len(family_trades),
            "hit_rate": round(wins / len(family_trades), 6) if family_trades else None,
            "total_pnl": round(sum(trade["pnl"] for trade in family_trades), 6),
        }
    return result
