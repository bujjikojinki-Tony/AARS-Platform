from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from statistics import fmean, pstdev
from typing import Sequence

from .features import compute_features
from .models import Candle
from .paper import PaperPortfolio
from .policy import decide_target_exposure
from .probability import estimate_outcome_probabilities
from .state_engine import classify_market_state


@dataclass(frozen=True)
class SimulationSummary:
    strategy: str
    symbol: str
    timeframe: str
    bars: int
    initial_equity: float
    final_equity: float
    total_return: float
    max_drawdown: float
    fees: float
    funding: float
    turnover_notional: float
    final_net_exposure: float
    sharpe_approx: float


def _sharpe(equities: Sequence[float], periods_per_year: int = 24 * 365) -> float:
    if len(equities) < 3:
        return 0.0
    returns = [b / a - 1.0 for a, b in zip(equities[:-1], equities[1:]) if a > 0]
    if len(returns) < 2:
        return 0.0
    sigma = pstdev(returns)
    if sigma == 0:
        return 0.0
    return fmean(returns) / sigma * sqrt(periods_per_year)


def simulate_aars_dynamic(
    candles: Sequence[Candle],
    *,
    initial_equity: float = 1000.0,
    warmup_bars: int = 120,
    max_abs_exposure: float = 1.0,
    fee_rate: float = 0.0005,
    slippage_rate: float = 0.0002,
) -> SimulationSummary:
    if len(candles) <= warmup_bars:
        raise ValueError("insufficient candles for simulation")
    portfolio = PaperPortfolio(
        initial_equity,
        fee_rate=fee_rate,
        slippage_rate=slippage_rate,
    )
    equities: list[float] = [initial_equity]
    turnover = 0.0

    for i in range(warmup_bars - 1, len(candles)):
        mark = candles[i].close
        features = compute_features(candles[: i + 1])
        assessment = classify_market_state(features)
        probabilities = estimate_outcome_probabilities(assessment, horizon_bars=24)
        decision = decide_target_exposure(
            assessment,
            probabilities,
            max_abs_exposure=max_abs_exposure,
        )
        delta = portfolio.rebalance_to_exposure(
            decision.target_exposure,
            mark,
            max_leverage=max_abs_exposure,
        )
        turnover += abs(delta) * mark
        equities.append(portfolio.snapshot(mark).equity)

    final = portfolio.snapshot(candles[-1].close)
    return SimulationSummary(
        strategy="AARS_DYNAMIC",
        symbol=candles[-1].symbol,
        timeframe=candles[-1].timeframe,
        bars=len(candles) - warmup_bars + 1,
        initial_equity=initial_equity,
        final_equity=final.equity,
        total_return=final.equity / initial_equity - 1.0,
        max_drawdown=final.max_drawdown,
        fees=final.fees,
        funding=final.funding,
        turnover_notional=turnover,
        final_net_exposure=final.net_exposure,
        sharpe_approx=_sharpe(equities),
    )


def simulate_buy_hold(
    candles: Sequence[Candle],
    *,
    initial_equity: float = 1000.0,
    warmup_bars: int = 120,
    fee_rate: float = 0.0005,
    slippage_rate: float = 0.0002,
) -> SimulationSummary:
    if len(candles) <= warmup_bars:
        raise ValueError("insufficient candles for simulation")
    portfolio = PaperPortfolio(
        initial_equity,
        fee_rate=fee_rate,
        slippage_rate=slippage_rate,
    )
    entry = candles[warmup_bars - 1].close
    delta = portfolio.rebalance_to_exposure(1.0, entry, max_leverage=1.0)
    turnover = abs(delta) * entry
    equities: list[float] = [initial_equity]
    for candle in candles[warmup_bars - 1 :]:
        equities.append(portfolio.snapshot(candle.close).equity)

    final = portfolio.snapshot(candles[-1].close)
    return SimulationSummary(
        strategy="BUY_HOLD",
        symbol=candles[-1].symbol,
        timeframe=candles[-1].timeframe,
        bars=len(candles) - warmup_bars + 1,
        initial_equity=initial_equity,
        final_equity=final.equity,
        total_return=final.equity / initial_equity - 1.0,
        max_drawdown=final.max_drawdown,
        fees=final.fees,
        funding=final.funding,
        turnover_notional=turnover,
        final_net_exposure=final.net_exposure,
        sharpe_approx=_sharpe(equities),
    )
