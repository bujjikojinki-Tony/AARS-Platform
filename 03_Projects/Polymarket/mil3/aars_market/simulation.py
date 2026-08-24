from __future__ import annotations

from dataclasses import asdict, dataclass
from math import sqrt
from statistics import fmean, pstdev
from typing import Protocol, Sequence

from .features import compute_features
from .models import Candle, MarketState
from .paper import PaperPortfolio
from .policy import decide_target_exposure
from .probability import estimate_outcome_probabilities
from .state_engine import classify_market_state


EXECUTION_MODE = "PAPER_ONLY"


@dataclass(frozen=True)
class StrategyAction:
    target_exposure: float
    price: float
    reason: str
    category: str = "rebalance"


class ShadowStrategy(Protocol):
    name: str
    max_leverage: float
    uses_funding: bool

    def reset(self) -> None: ...

    def actions_for_bar(
        self,
        index: int,
        candles: Sequence[Candle],
    ) -> list[StrategyAction]: ...


@dataclass(frozen=True)
class SimulationSummary:
    strategy: str
    execution_mode: str
    symbol: str
    timeframe: str
    bars: int
    initial_equity: float
    final_equity: float
    total_return: float
    max_drawdown: float
    sharpe_approx: float
    sortino: float
    profit_factor: float
    turnover_notional: float
    fees: float
    slippage: float
    funding: float
    realized_pnl: float
    realized_grid_pnl: float
    inventory_unrealized_pnl: float
    final_net_exposure: float
    max_abs_net_exposure: float
    final_effective_leverage: float
    max_effective_leverage: float
    min_margin_buffer_pct: float
    max_liquidation_risk: float
    liquidation_events: int

    def as_dict(self) -> dict[str, float | int | str]:
        return asdict(self)


def _periods_per_year(timeframe: str) -> int:
    unit = timeframe[-1:].lower()
    try:
        count = int(timeframe[:-1])
    except (TypeError, ValueError):
        return 24 * 365
    if count <= 0:
        return 24 * 365
    if unit == "m":
        return max(1, int(365 * 24 * 60 / count))
    if unit == "h":
        return max(1, int(365 * 24 / count))
    if unit == "d":
        return max(1, int(365 / count))
    return 24 * 365


def _returns(equities: Sequence[float]) -> list[float]:
    return [b / a - 1.0 for a, b in zip(equities[:-1], equities[1:]) if a > 0]


def _sharpe(equities: Sequence[float], periods_per_year: int) -> float:
    returns = _returns(equities)
    if len(returns) < 2:
        return 0.0
    sigma = pstdev(returns)
    return fmean(returns) / sigma * sqrt(periods_per_year) if sigma else 0.0


def _sortino(equities: Sequence[float], periods_per_year: int) -> float:
    returns = _returns(equities)
    if len(returns) < 2:
        return 0.0
    downside = [min(value, 0.0) for value in returns]
    downside_deviation = sqrt(fmean(value * value for value in downside))
    return fmean(returns) / downside_deviation * sqrt(periods_per_year) if downside_deviation else 0.0


def _profit_factor(equities: Sequence[float]) -> float:
    changes = [b - a for a, b in zip(equities[:-1], equities[1:])]
    gross_profit = sum(value for value in changes if value > 0)
    gross_loss = -sum(value for value in changes if value < 0)
    if gross_loss == 0:
        return float("inf") if gross_profit > 0 else 0.0
    return gross_profit / gross_loss


class BuyAndHoldStrategy:
    name = "BUY_HOLD"
    max_leverage = 1.0
    uses_funding = False

    def __init__(self) -> None:
        self._entered = False

    def reset(self) -> None:
        self._entered = False

    def actions_for_bar(self, index: int, candles: Sequence[Candle]) -> list[StrategyAction]:
        if self._entered:
            return []
        self._entered = True
        return [StrategyAction(1.0, candles[index].close, "one-time spot entry", "entry")]


class GridStrategy:
    uses_funding = False

    def __init__(
        self,
        *,
        name: str,
        max_leverage: float,
        spacing_pct: float = 0.01,
        levels: int = 5,
    ) -> None:
        if max_leverage <= 0:
            raise ValueError("max_leverage must be positive")
        if spacing_pct <= 0:
            raise ValueError("spacing_pct must be positive")
        if levels <= 0:
            raise ValueError("levels must be positive")
        self.name = name
        self.max_leverage = float(max_leverage)
        self.spacing_pct = float(spacing_pct)
        self.levels = int(levels)
        self._anchor: float | None = None
        self._grid_target = self.max_leverage / 2.0
        self._hedging = False

    def reset(self) -> None:
        self._anchor = None
        self._grid_target = self.max_leverage / 2.0
        self._hedging = False

    def _price_for_level(self, level: int) -> float:
        assert self._anchor is not None
        return self._anchor * (1.0 + self.spacing_pct) ** level

    def _target_for_level(self, level: int) -> float:
        step = self.max_leverage / (2.0 * self.levels)
        return max(0.0, min(self.max_leverage, self.max_leverage / 2.0 - level * step))

    def _crossed_levels(self, start: float, end: float) -> list[int]:
        if start == end:
            return []
        levels = range(-self.levels, self.levels + 1)
        if end > start:
            return sorted(level for level in levels if start < self._price_for_level(level) <= end)
        return sorted(
            (level for level in levels if end <= self._price_for_level(level) < start),
            reverse=True,
        )

    @staticmethod
    def _intrabar_path(candle: Candle, previous_close: float) -> list[float]:
        middle = [candle.low, candle.high] if candle.close >= candle.open else [candle.high, candle.low]
        return [previous_close, candle.open, *middle, candle.close]

    def _grid_actions(self, index: int, candles: Sequence[Candle]) -> list[StrategyAction]:
        candle = candles[index]
        if self._anchor is None:
            self._anchor = candle.close
            self._grid_target = self.max_leverage / 2.0
            return [StrategyAction(self._grid_target, candle.close, "initialize symmetric grid", "grid")]

        previous_close = candles[index - 1].close if index > 0 else candle.open
        path = self._intrabar_path(candle, previous_close)
        actions: list[StrategyAction] = []
        for start, end in zip(path[:-1], path[1:]):
            for level in self._crossed_levels(start, end):
                target = self._target_for_level(level)
                if abs(target - self._grid_target) < 1e-12:
                    continue
                self._grid_target = target
                actions.append(
                    StrategyAction(
                        target,
                        self._price_for_level(level),
                        f"grid level {level:+d}",
                        "grid",
                    )
                )
        return actions

    def actions_for_bar(self, index: int, candles: Sequence[Candle]) -> list[StrategyAction]:
        return self._grid_actions(index, candles)


class SpotGridStrategy(GridStrategy):
    def __init__(self, *, spacing_pct: float = 0.01, levels: int = 5) -> None:
        super().__init__(name="SPOT_GRID", max_leverage=1.0, spacing_pct=spacing_pct, levels=levels)


class LeveragedFuturesLongGridStrategy(GridStrategy):
    uses_funding = True

    def __init__(
        self,
        *,
        max_leverage: float = 10.0,
        spacing_pct: float = 0.01,
        levels: int = 5,
        tactical_hedge: bool = True,
        hedge_ratio: float = 0.20,
    ) -> None:
        if not 0 <= hedge_ratio <= 1:
            raise ValueError("hedge_ratio must be between 0 and 1")
        super().__init__(
            name=f"FUTURES_LONG_GRID_{max_leverage:g}X",
            max_leverage=max_leverage,
            spacing_pct=spacing_pct,
            levels=levels,
        )
        self.tactical_hedge = tactical_hedge
        self.hedge_ratio = hedge_ratio

    def actions_for_bar(self, index: int, candles: Sequence[Candle]) -> list[StrategyAction]:
        candle = candles[index]
        assessment = None
        if self.tactical_hedge and index >= 59:
            assessment = classify_market_state(compute_features(candles[: index + 1]))

        if assessment and assessment.state == MarketState.BREAKDOWN:
            self._hedging = True
            return [
                StrategyAction(
                    -self.max_leverage * self.hedge_ratio,
                    candle.close,
                    "tactical hedge: BREAKDOWN",
                    "hedge",
                )
            ]
        if assessment and assessment.state == MarketState.DISTRIBUTION:
            self._hedging = True
            return [StrategyAction(0.0, candle.close, "tactical hedge: DISTRIBUTION", "hedge")]

        actions = self._grid_actions(index, candles)
        if self._hedging:
            self._hedging = False
            if not actions:
                actions.append(
                    StrategyAction(
                        self._grid_target,
                        candle.close,
                        "release tactical hedge to grid target",
                        "hedge_release",
                    )
                )
        return actions


class AarsDynamicStrategy:
    name = "AARS_DYNAMIC"
    uses_funding = True

    def __init__(self, *, max_abs_exposure: float = 1.0) -> None:
        if max_abs_exposure <= 0:
            raise ValueError("max_abs_exposure must be positive")
        self.max_leverage = float(max_abs_exposure)

    def reset(self) -> None:
        return None

    def actions_for_bar(self, index: int, candles: Sequence[Candle]) -> list[StrategyAction]:
        features = compute_features(candles[: index + 1])
        assessment = classify_market_state(features)
        probabilities = estimate_outcome_probabilities(assessment, horizon_bars=24)
        decision = decide_target_exposure(
            assessment,
            probabilities,
            max_abs_exposure=self.max_leverage,
        )
        category = "tactical_short" if decision.target_exposure < 0 else "rebalance"
        return [StrategyAction(decision.target_exposure, candles[index].close, decision.reason, category)]


class ReplayEngine:
    """One PAPER_ONLY accounting path for every shadow strategy."""

    def __init__(
        self,
        *,
        initial_equity: float = 1000.0,
        fee_rate: float = 0.0005,
        slippage_rate: float = 0.0002,
        funding_rate_per_bar: float = 0.0,
        maintenance_margin_rate: float = 0.005,
    ) -> None:
        if maintenance_margin_rate < 0:
            raise ValueError("maintenance_margin_rate must be non-negative")
        self.initial_equity = initial_equity
        self.fee_rate = fee_rate
        self.slippage_rate = slippage_rate
        self.funding_rate_per_bar = funding_rate_per_bar
        self.maintenance_margin_rate = maintenance_margin_rate

    def run(
        self,
        candles: Sequence[Candle],
        strategy: ShadowStrategy,
        *,
        warmup_bars: int = 120,
    ) -> SimulationSummary:
        if len(candles) <= warmup_bars:
            raise ValueError("insufficient candles for simulation")
        if warmup_bars < 60:
            raise ValueError("warmup_bars must be at least 60")
        portfolio = PaperPortfolio(
            self.initial_equity,
            fee_rate=self.fee_rate,
            slippage_rate=self.slippage_rate,
        )
        strategy.reset()
        equities: list[float] = [self.initial_equity]
        turnover = 0.0
        realized_grid_pnl = 0.0
        max_abs_exposure = 0.0
        max_leverage = 0.0
        min_margin_buffer = 1.0
        max_liquidation_risk = 0.0
        liquidation_events = 0
        last_mark = candles[warmup_bars - 1].close

        for index in range(warmup_bars - 1, len(candles)):
            candle = candles[index]
            last_mark = candle.close
            for action in strategy.actions_for_bar(index, candles):
                trade = portfolio.rebalance_to_exposure(
                    action.target_exposure,
                    action.price,
                    max_leverage=strategy.max_leverage,
                )
                if trade is None:
                    continue
                turnover += trade.notional
                if action.category == "grid":
                    realized_grid_pnl += trade.realized_pnl_delta

            if strategy.uses_funding and self.funding_rate_per_bar:
                portfolio.apply_funding_rate(candle.close, self.funding_rate_per_bar)

            snapshot = portfolio.snapshot(
                candle.close,
                maintenance_margin_rate=self.maintenance_margin_rate,
            )
            equities.append(snapshot.equity)
            max_abs_exposure = max(max_abs_exposure, abs(snapshot.net_exposure))
            max_leverage = max(max_leverage, snapshot.effective_leverage)
            if snapshot.position_qty:
                min_margin_buffer = min(min_margin_buffer, snapshot.margin_buffer_pct)
            max_liquidation_risk = max(max_liquidation_risk, snapshot.liquidation_risk)
            liquidation_events += int(snapshot.liquidation_breached)
            if snapshot.equity <= 0:
                break

        final = portfolio.snapshot(
            last_mark,
            maintenance_margin_rate=self.maintenance_margin_rate,
        )
        periods = _periods_per_year(candles[-1].timeframe)
        return SimulationSummary(
            strategy=strategy.name,
            execution_mode=EXECUTION_MODE,
            symbol=candles[-1].symbol,
            timeframe=candles[-1].timeframe,
            bars=len(equities) - 1,
            initial_equity=self.initial_equity,
            final_equity=final.equity,
            total_return=final.equity / self.initial_equity - 1.0,
            max_drawdown=final.max_drawdown,
            sharpe_approx=_sharpe(equities, periods),
            sortino=_sortino(equities, periods),
            profit_factor=_profit_factor(equities),
            turnover_notional=turnover,
            fees=final.fees,
            slippage=final.slippage_cost,
            funding=final.funding,
            realized_pnl=final.realized_pnl,
            realized_grid_pnl=realized_grid_pnl,
            inventory_unrealized_pnl=final.unrealized_pnl,
            final_net_exposure=final.net_exposure,
            max_abs_net_exposure=max_abs_exposure,
            final_effective_leverage=final.effective_leverage,
            max_effective_leverage=max_leverage,
            min_margin_buffer_pct=min_margin_buffer,
            max_liquidation_risk=max_liquidation_risk,
            liquidation_events=liquidation_events,
        )


def compare_shadow_strategies(
    candles: Sequence[Candle],
    *,
    initial_equity: float = 1000.0,
    warmup_bars: int = 120,
    futures_leverage: float = 10.0,
    aars_max_abs_exposure: float = 1.0,
    grid_spacing_pct: float = 0.01,
    grid_levels: int = 5,
    tactical_hedge: bool = True,
    fee_rate: float = 0.0005,
    slippage_rate: float = 0.0002,
    funding_rate_per_bar: float = 0.0,
    maintenance_margin_rate: float = 0.005,
) -> list[SimulationSummary]:
    engine = ReplayEngine(
        initial_equity=initial_equity,
        fee_rate=fee_rate,
        slippage_rate=slippage_rate,
        funding_rate_per_bar=funding_rate_per_bar,
        maintenance_margin_rate=maintenance_margin_rate,
    )
    strategies: list[ShadowStrategy] = [
        BuyAndHoldStrategy(),
        SpotGridStrategy(spacing_pct=grid_spacing_pct, levels=grid_levels),
        LeveragedFuturesLongGridStrategy(
            max_leverage=futures_leverage,
            spacing_pct=grid_spacing_pct,
            levels=grid_levels,
            tactical_hedge=tactical_hedge,
        ),
        AarsDynamicStrategy(max_abs_exposure=aars_max_abs_exposure),
    ]
    return [engine.run(candles, strategy, warmup_bars=warmup_bars) for strategy in strategies]


def simulate_aars_dynamic(
    candles: Sequence[Candle],
    *,
    initial_equity: float = 1000.0,
    warmup_bars: int = 120,
    max_abs_exposure: float = 1.0,
    fee_rate: float = 0.0005,
    slippage_rate: float = 0.0002,
    funding_rate_per_bar: float = 0.0,
) -> SimulationSummary:
    engine = ReplayEngine(
        initial_equity=initial_equity,
        fee_rate=fee_rate,
        slippage_rate=slippage_rate,
        funding_rate_per_bar=funding_rate_per_bar,
    )
    return engine.run(
        candles,
        AarsDynamicStrategy(max_abs_exposure=max_abs_exposure),
        warmup_bars=warmup_bars,
    )


def simulate_buy_hold(
    candles: Sequence[Candle],
    *,
    initial_equity: float = 1000.0,
    warmup_bars: int = 120,
    fee_rate: float = 0.0005,
    slippage_rate: float = 0.0002,
) -> SimulationSummary:
    engine = ReplayEngine(
        initial_equity=initial_equity,
        fee_rate=fee_rate,
        slippage_rate=slippage_rate,
    )
    return engine.run(candles, BuyAndHoldStrategy(), warmup_bars=warmup_bars)
