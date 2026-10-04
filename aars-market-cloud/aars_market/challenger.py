from __future__ import annotations

from math import isfinite
from typing import Any, Mapping

from .diagnostics import _select_snapshot, _utc, build_strategy_diagnostics
from .models import MarketState
from .service import WINDOWS
from .simulation import (
    AarsDeadbandStrategy,
    AarsDynamicStrategy,
    ReplayEngine,
    ReplayResult,
)
from .storage import MarketStore


SCHEMA_VERSION = "mil3.low-turnover-challenger.v1"
EXECUTION_MODE = "PAPER_ONLY"


def _authority() -> dict[str, bool]:
    return {
        "read_only": True,
        "challenger_activation_allowed": False,
        "automatic_strategy_change_allowed": False,
        "paper_configuration_activation_allowed": False,
        "live_execution_allowed": False,
    }


def _degraded(reason: str, snapshot_id: str | None = None) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "execution_mode": EXECUTION_MODE,
        "status": "DEGRADED",
        "data_trust": {
            "status": "UNAVAILABLE",
            "reason": reason,
            "source_snapshot_id": snapshot_id,
        },
        "authority": _authority(),
        "configuration": None,
        "comparison": None,
        "assets": [],
        "review_gate": {
            "disposition": "DEFER",
            "reasons": [reason],
            "requires_independent_validation": True,
            "live_execution_allowed": False,
        },
    }


def _finite(value: float) -> float | None:
    return value if isfinite(value) else None


def _turnover_reduction(baseline: float, challenger: float) -> float:
    if baseline <= 1e-12:
        return 0.0
    return 1.0 - challenger / baseline


def _aggregate(
    results: Mapping[str, ReplayResult], weights: Mapping[str, float]
) -> dict[str, Any]:
    trace = {
        symbol: {point.as_of: point for point in result.trace}
        for symbol, result in results.items()
    }
    common = sorted(set.intersection(*(set(points) for points in trace.values())))
    peak = 1.0
    max_drawdown = 0.0
    for as_of in common:
        equity_index = sum(
            weights[symbol]
            * trace[symbol][as_of].equity
            / results[symbol].summary.initial_equity
            for symbol in results
        )
        peak = max(peak, equity_index)
        max_drawdown = max(
            max_drawdown,
            max(0.0, 1.0 - equity_index / peak) if peak > 0 else 1.0,
        )
    return {
        "total_return": sum(
            weights[symbol] * result.summary.total_return
            for symbol, result in results.items()
        ),
        "max_drawdown": max_drawdown,
        "turnover_multiple": sum(
            weights[symbol]
            * result.summary.turnover_notional
            / result.summary.initial_equity
            for symbol, result in results.items()
        ),
        "fills": sum(len(result.fills) for result in results.values()),
        "modeled_cost_return": sum(
            weights[symbol]
            * (
                result.summary.fees
                + result.summary.slippage
                + result.summary.funding
            )
            / result.summary.initial_equity
            for symbol, result in results.items()
        ),
        "fees": sum(
            weights[symbol] * result.summary.fees
            for symbol, result in results.items()
        ),
        "slippage": sum(
            weights[symbol] * result.summary.slippage
            for symbol, result in results.items()
        ),
        "funding": sum(
            weights[symbol] * result.summary.funding
            for symbol, result in results.items()
        ),
        "max_effective_leverage": max(
            result.summary.max_effective_leverage for result in results.values()
        ),
        "min_margin_buffer_pct": min(
            result.summary.min_margin_buffer_pct for result in results.values()
        ),
        "max_liquidation_risk": max(
            result.summary.max_liquidation_risk for result in results.values()
        ),
        "liquidation_events": sum(
            result.summary.liquidation_events for result in results.values()
        ),
    }


def _asset_result(actual: ReplayResult, zero_cost: ReplayResult) -> dict[str, Any]:
    total_cost = actual.summary.fees + actual.summary.slippage + actual.summary.funding
    return {
        "actual_cost": {
            "total_return": actual.summary.total_return,
            "max_drawdown": actual.summary.max_drawdown,
            "sharpe": _finite(actual.summary.sharpe_approx),
            "sortino": _finite(actual.summary.sortino),
            "turnover_multiple": (
                actual.summary.turnover_notional / actual.summary.initial_equity
            ),
            "fills": len(actual.fills),
            "fees": actual.summary.fees,
            "slippage": actual.summary.slippage,
            "funding": actual.summary.funding,
            "modeled_cost_return": total_cost / actual.summary.initial_equity,
            "max_liquidation_risk": actual.summary.max_liquidation_risk,
            "liquidation_events": actual.summary.liquidation_events,
        },
        "zero_cost": {
            "total_return": zero_cost.summary.total_return,
            "max_drawdown": zero_cost.summary.max_drawdown,
            "sharpe": _finite(zero_cost.summary.sharpe_approx),
            "sortino": _finite(zero_cost.summary.sortino),
            "turnover_multiple": (
                zero_cost.summary.turnover_notional / zero_cost.summary.initial_equity
            ),
            "fills": len(zero_cost.fills),
            "fees": zero_cost.summary.fees,
            "slippage": zero_cost.summary.slippage,
            "funding": zero_cost.summary.funding,
        },
        "true_zero_cost_effect": (
            zero_cost.summary.total_return - actual.summary.total_return
        ),
    }


def build_low_turnover_challenger(
    store: MarketStore,
    *,
    snapshot_id: str | None = None,
    min_rebalance_bars: int = 12,
    challenger_exposure_scale: float = 0.95,
    state_deadbands: Mapping[MarketState, float] | None = None,
) -> dict[str, Any]:
    """Compare baseline and deadband challenger without changing authority."""
    diagnostic = build_strategy_diagnostics(store, snapshot_id=snapshot_id)
    if diagnostic["status"] != "READY":
        return _degraded(
            f"SOURCE_DIAGNOSTIC_{diagnostic['data_trust']['reason']}",
            diagnostic["data_trust"].get("source_snapshot_id") or snapshot_id,
        )
    source_id = str(diagnostic["data_trust"]["source_snapshot_id"])
    selected = _select_snapshot(store, source_id)
    if selected is None:
        return _degraded("SOURCE_SNAPSHOT_NOT_FOUND", source_id)
    _, snapshot = selected
    configuration = snapshot["configuration"]
    as_of = _utc(snapshot["as_of"])
    timeframe = str(configuration["timeframe"])
    replay_window = str(configuration["replay_window"])
    duration = WINDOWS[replay_window]
    start = as_of - duration if duration is not None else None
    warmup_bars = int(configuration["warmup_bars"])
    weights = {
        str(symbol): float(weight)
        for symbol, weight in snapshot["portfolio"]["weights"].items()
    }

    baseline_actual: dict[str, ReplayResult] = {}
    baseline_zero: dict[str, ReplayResult] = {}
    challenger_actual: dict[str, ReplayResult] = {}
    challenger_zero: dict[str, ReplayResult] = {}
    assets: list[dict[str, Any]] = []
    for symbol in snapshot["symbols"]:
        candles = store.load_candles(symbol, timeframe, start=start, end=as_of)
        funding = store.load_funding_rates(
            symbol, start=candles[0].open_time, end=as_of
        )
        actual_engine = ReplayEngine(funding_rates=funding)
        zero_engine = ReplayEngine(
            fee_rate=0.0,
            slippage_rate=0.0,
            funding_rate_per_bar=0.0,
            funding_rates=(),
        )
        baseline_actual[symbol] = actual_engine.run_detailed(
            candles, AarsDynamicStrategy(), warmup_bars=warmup_bars
        )
        baseline_zero[symbol] = zero_engine.run_detailed(
            candles, AarsDynamicStrategy(), warmup_bars=warmup_bars
        )
        challenger_actual[symbol] = actual_engine.run_detailed(
            candles,
            AarsDeadbandStrategy(
                exposure_scale=challenger_exposure_scale,
                min_rebalance_bars=min_rebalance_bars,
                state_deadbands=state_deadbands,
            ),
            warmup_bars=warmup_bars,
        )
        challenger_zero[symbol] = zero_engine.run_detailed(
            candles,
            AarsDeadbandStrategy(
                exposure_scale=challenger_exposure_scale,
                min_rebalance_bars=min_rebalance_bars,
                state_deadbands=state_deadbands,
            ),
            warmup_bars=warmup_bars,
        )
        baseline_asset = _asset_result(
            baseline_actual[symbol], baseline_zero[symbol]
        )
        challenger_asset = _asset_result(
            challenger_actual[symbol], challenger_zero[symbol]
        )
        assets.append(
            {
                "symbol": symbol,
                "weight": weights[symbol],
                "baseline": baseline_asset,
                "challenger": challenger_asset,
                "deltas": {
                    "actual_return": (
                        challenger_asset["actual_cost"]["total_return"]
                        - baseline_asset["actual_cost"]["total_return"]
                    ),
                    "zero_cost_return": (
                        challenger_asset["zero_cost"]["total_return"]
                        - baseline_asset["zero_cost"]["total_return"]
                    ),
                    "turnover_reduction": (
                        _turnover_reduction(
                            baseline_asset["actual_cost"]["turnover_multiple"],
                            challenger_asset["actual_cost"]["turnover_multiple"],
                        )
                    ),
                    "true_cost_effect_reduction": (
                        baseline_asset["true_zero_cost_effect"]
                        - challenger_asset["true_zero_cost_effect"]
                    ),
                },
            }
        )

    aggregate_baseline_actual = _aggregate(baseline_actual, weights)
    aggregate_baseline_zero = _aggregate(baseline_zero, weights)
    aggregate_challenger_actual = _aggregate(challenger_actual, weights)
    aggregate_challenger_zero = _aggregate(challenger_zero, weights)
    turnover_reduction = _turnover_reduction(
        aggregate_baseline_actual["turnover_multiple"],
        aggregate_challenger_actual["turnover_multiple"],
    )
    actual_return_delta = (
        aggregate_challenger_actual["total_return"]
        - aggregate_baseline_actual["total_return"]
    )
    zero_cost_return_delta = (
        aggregate_challenger_zero["total_return"]
        - aggregate_baseline_zero["total_return"]
    )
    baseline_true_cost_effect = (
        aggregate_baseline_zero["total_return"]
        - aggregate_baseline_actual["total_return"]
    )
    challenger_true_cost_effect = (
        aggregate_challenger_zero["total_return"]
        - aggregate_challenger_actual["total_return"]
    )
    checks = [
        {
            "id": "TURNOVER_REDUCTION",
            "status": "PASS" if turnover_reduction >= 0.50 else "BLOCK",
            "observed": turnover_reduction,
            "requirement": ">= 50%",
            "impact": "Insufficient reduction leaves the strategy dominated by rebalance costs.",
            "recovery_condition": "A fixed independent challenger reduces turnover by at least 50%.",
        },
        {
            "id": "ACTUAL_RETURN_DELTA",
            "status": "PASS" if actual_return_delta >= 0 else "BLOCK",
            "observed": actual_return_delta,
            "requirement": ">= 0%",
            "impact": "A lower actual-cost return does not address the diagnosed performance drag.",
            "recovery_condition": "Challenger actual-cost return is no worse on identical evidence.",
        },
        {
            "id": "DRAWDOWN_DELTA",
            "status": "PASS"
            if aggregate_challenger_actual["max_drawdown"]
            - aggregate_baseline_actual["max_drawdown"]
            <= 0.02
            else "BLOCK",
            "observed": (
                aggregate_challenger_actual["max_drawdown"]
                - aggregate_baseline_actual["max_drawdown"]
            ),
            "requirement": "<= +2 percentage points",
            "impact": "Turnover savings must not materially worsen portfolio drawdown.",
            "recovery_condition": "Drawdown increase is no more than two percentage points.",
        },
        {
            "id": "LIQUIDATION_RISK",
            "status": "PASS"
            if aggregate_challenger_actual["liquidation_events"] == 0
            and aggregate_challenger_actual["max_liquidation_risk"]
            <= aggregate_baseline_actual["max_liquidation_risk"] + 1e-12
            else "BLOCK",
            "observed": aggregate_challenger_actual["max_liquidation_risk"],
            "requirement": "zero events and no increase",
            "impact": "A cost improvement cannot be accepted by adding liquidation risk.",
            "recovery_condition": "Zero events and risk no higher than the verified baseline.",
        },
    ]
    blocking = [item["id"] for item in checks if item["status"] != "PASS"]
    materially_adverse = (
        actual_return_delta < -0.05
        or aggregate_challenger_actual["max_drawdown"]
        - aggregate_baseline_actual["max_drawdown"]
        > 0.05
    )
    disposition = (
        "PROMISING_CHALLENGER"
        if not blocking
        else "REJECT_CHALLENGER"
        if materially_adverse
        else "CONTINUE_RESEARCH"
    )
    configured_deadbands = dict(
        state_deadbands or AarsDeadbandStrategy.DEFAULT_DEADBANDS
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "execution_mode": EXECUTION_MODE,
        "status": "READY",
        "data_trust": {
            **diagnostic["data_trust"],
            "comparison_boundary": "IDENTICAL_FULLY_CLOSED_V2_EVIDENCE",
        },
        "authority": _authority(),
        "configuration": {
            "baseline_strategy": "AARS_DYNAMIC",
            "challenger_strategy": "AARS_DEADBAND_CHALLENGER",
            "challenger_exposure_scale": challenger_exposure_scale,
            "min_rebalance_bars": min_rebalance_bars,
            "state_deadbands": {
                state.value: configured_deadbands[state] for state in MarketState
            },
            "risk_transition_bypass": [
                state.value for state in sorted(
                    AarsDeadbandStrategy.RISK_STATES, key=lambda item: item.value
                )
            ],
            "sign_change_bypass": True,
            "actual_cost_model": {
                "fee_rate": 0.0005,
                "slippage_rate": 0.0002,
                "funding": "archived Binance public funding history",
            },
            "zero_cost_model": {
                "fee_rate": 0.0,
                "slippage_rate": 0.0,
                "funding_rate": 0.0,
                "kind": "TRUE_ENGINE_RERUN_NOT_ACCOUNTING_ADD_BACK",
            },
        },
        "comparison": {
            "baseline": {
                "actual_cost": aggregate_baseline_actual,
                "zero_cost": aggregate_baseline_zero,
                "true_zero_cost_effect": baseline_true_cost_effect,
            },
            "challenger": {
                "actual_cost": aggregate_challenger_actual,
                "zero_cost": aggregate_challenger_zero,
                "true_zero_cost_effect": challenger_true_cost_effect,
            },
            "deltas": {
                "actual_return": actual_return_delta,
                "zero_cost_policy_return": zero_cost_return_delta,
                "turnover_reduction": turnover_reduction,
                "true_cost_effect_reduction": (
                    baseline_true_cost_effect - challenger_true_cost_effect
                ),
                "max_drawdown": (
                    aggregate_challenger_actual["max_drawdown"]
                    - aggregate_baseline_actual["max_drawdown"]
                ),
                "liquidation_risk": (
                    aggregate_challenger_actual["max_liquidation_risk"]
                    - aggregate_baseline_actual["max_liquidation_risk"]
                ),
            },
            "interpretation_limits": [
                "Zero-cost results are separate engine reruns, not fee add-backs.",
                "Zero-cost policy delta isolates strategy behavior only within this replay model.",
                "A favorable challenger is not configuration or execution authority.",
            ],
        },
        "assets": assets,
        "review_gate": {
            "disposition": disposition,
            "checks": checks,
            "blocking_checks": blocking,
            "requires_independent_validation": True,
            "proposal_creation_allowed": False,
            "automatic_strategy_change_allowed": False,
            "live_execution_allowed": False,
        },
    }
