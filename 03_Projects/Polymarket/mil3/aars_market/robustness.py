from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from statistics import fmean
from typing import Any, Mapping, Sequence

from .challenger import _aggregate, _turnover_reduction
from .diagnostics import _select_snapshot, _utc, build_strategy_diagnostics
from .models import Candle, FundingRate, MarketState
from .runtime_ledger import latest_synchronized_closed_boundary, timeframe_duration
from .simulation import AarsDeadbandStrategy, AarsDynamicStrategy, ReplayEngine, ReplayResult
from .storage import MarketStore


SCHEMA_VERSION = "mil3.frozen-challenger-robustness.v1"
EXECUTION_MODE = "PAPER_ONLY"
_STATE_PATTERN = re.compile(r"(?:^|;)\s*state=([A-Z_]+)")
FROZEN_DEADBANDS: Mapping[MarketState, float] = {
    MarketState.ACCUMULATION: 0.12,
    MarketState.RECOVERY: 0.10,
    MarketState.RANGE: 0.20,
    MarketState.BREAKOUT: 0.08,
    MarketState.TREND_EXPANSION: 0.08,
    MarketState.DISTRIBUTION: 0.05,
    MarketState.BREAKDOWN: 0.05,
}


@dataclass(frozen=True)
class RobustnessSettings:
    warmup_bars: int = 120
    test_bars: int = 168
    step_bars: int = 168
    discovery_window_bars: int = 90 * 24
    multi_windows: tuple[tuple[str, int], ...] = (
        ("30d", 30 * 24),
        ("60d", 60 * 24),
        ("90d", 90 * 24),
        ("120d", 120 * 24),
    )
    min_post_freeze_folds: int = 4

    def __post_init__(self) -> None:
        if self.warmup_bars < 60:
            raise ValueError("warmup_bars must be at least 60")
        if min(self.test_bars, self.step_bars, self.discovery_window_bars) <= 0:
            raise ValueError("fold and discovery sizes must be positive")
        if not self.multi_windows or any(bars <= self.warmup_bars for _, bars in self.multi_windows):
            raise ValueError("multi windows must exceed warmup")
        if self.min_post_freeze_folds <= 0:
            raise ValueError("min_post_freeze_folds must be positive")


STRESS_SCENARIOS: tuple[dict[str, float | str], ...] = (
    {"id": "ACTUAL_1X", "fee_multiplier": 1.0, "slippage_multiplier": 1.0, "funding_multiplier": 1.0},
    {"id": "EXECUTION_2X", "fee_multiplier": 2.0, "slippage_multiplier": 2.0, "funding_multiplier": 1.0},
    {"id": "EXECUTION_3X", "fee_multiplier": 3.0, "slippage_multiplier": 3.0, "funding_multiplier": 1.0},
    {"id": "ALL_MODELED_COST_2X", "fee_multiplier": 2.0, "slippage_multiplier": 2.0, "funding_multiplier": 2.0},
)


def _authority() -> dict[str, bool]:
    return {
        "read_only": True,
        "parameter_tuning_allowed": False,
        "proposal_creation_allowed": False,
        "challenger_activation_allowed": False,
        "automatic_strategy_change_allowed": False,
        "live_execution_allowed": False,
    }


def _degraded(reason: str, snapshot_id: str | None = None) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "execution_mode": EXECUTION_MODE,
        "status": "DEGRADED",
        "data_trust": {"status": "UNAVAILABLE", "reason": reason, "source_snapshot_id": snapshot_id},
        "authority": _authority(),
        "frozen_specification": None,
        "multi_window": [],
        "walk_forward": None,
        "market_state_evidence": [],
        "stress_matrix": [],
        "overfit_assessment": {"level": "UNKNOWN", "reason": reason},
        "review_gate": {
            "disposition": "DEFER",
            "blocking_checks": [reason],
            "parameter_tuning_allowed": False,
            "proposal_creation_allowed": False,
            "live_execution_allowed": False,
        },
    }


def frozen_specification(source_snapshot_id: str, frozen_at: str) -> dict[str, Any]:
    parameters = {
        "strategy": "AARS_DEADBAND_CHALLENGER",
        "max_abs_exposure": 1.0,
        "exposure_scale": 0.95,
        "min_rebalance_bars": 12,
        "state_deadbands": {
            state.value: FROZEN_DEADBANDS[state] for state in MarketState
        },
        "sign_change_bypass": True,
        "risk_transition_bypass": ["BREAKDOWN", "DISTRIBUTION"],
    }
    identity = {
        "schema_version": "mil3.frozen-challenger-spec.v1",
        "source_snapshot_id": source_snapshot_id,
        "frozen_at": frozen_at,
        "parameters": parameters,
    }
    canonical = json.dumps(identity, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return {
        **identity,
        "spec_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "immutable": True,
        "validation_time_tuning_allowed": False,
    }


def _scaled_funding(rates: Sequence[FundingRate], multiplier: float) -> tuple[FundingRate, ...]:
    return tuple(
        FundingRate(
            item.symbol,
            item.funding_time,
            item.funding_rate * multiplier,
            item.mark_price,
            item.rate_type,
        )
        for item in rates
    )


def _run_pair(
    candles: Sequence[Candle],
    funding: Sequence[FundingRate],
    *,
    warmup_bars: int,
    fee_multiplier: float = 1.0,
    slippage_multiplier: float = 1.0,
    funding_multiplier: float = 1.0,
) -> tuple[ReplayResult, ReplayResult]:
    engine = ReplayEngine(
        fee_rate=0.0005 * fee_multiplier,
        slippage_rate=0.0002 * slippage_multiplier,
        funding_rates=_scaled_funding(funding, funding_multiplier),
    )
    baseline = engine.run_detailed(candles, AarsDynamicStrategy(), warmup_bars=warmup_bars)
    challenger = engine.run_detailed(
        candles,
        AarsDeadbandStrategy(
            exposure_scale=0.95,
            min_rebalance_bars=12,
            state_deadbands=FROZEN_DEADBANDS,
        ),
        warmup_bars=warmup_bars,
    )
    return baseline, challenger


def _comparison(
    baseline: Mapping[str, ReplayResult],
    challenger: Mapping[str, ReplayResult],
    weights: Mapping[str, float],
) -> dict[str, Any]:
    before = _aggregate(baseline, weights)
    after = _aggregate(challenger, weights)
    return {
        "baseline": before,
        "challenger": after,
        "deltas": {
            "total_return": after["total_return"] - before["total_return"],
            "max_drawdown": after["max_drawdown"] - before["max_drawdown"],
            "turnover_reduction": _turnover_reduction(
                before["turnover_multiple"], after["turnover_multiple"]
            ),
            "modeled_cost_return": after["modeled_cost_return"] - before["modeled_cost_return"],
            "liquidation_risk": after["max_liquidation_risk"] - before["max_liquidation_risk"],
        },
    }


def _state_attribution(
    baseline: ReplayResult, challenger: ReplayResult
) -> dict[str, dict[str, float | int]]:
    states: dict[int, str] = {}
    for fill in baseline.fills:
        matched = _STATE_PATTERN.search(fill.reason)
        if matched:
            states[fill.index] = matched.group(1)
    challenger_by_time = {point.as_of: point for point in challenger.trace}
    result: dict[str, dict[str, float | int]] = defaultdict(
        lambda: {"bars": 0, "baseline_return": 0.0, "challenger_return": 0.0}
    )
    baseline_previous = baseline.summary.initial_equity
    challenger_previous = challenger.summary.initial_equity
    last_state = "UNKNOWN"
    for point in baseline.trace:
        if point.index in states:
            last_state = states[point.index]
        challenger_point = challenger_by_time[point.as_of]
        bucket = result[last_state]
        bucket["bars"] += 1
        bucket["baseline_return"] += (
            point.equity - baseline_previous
        ) / baseline.summary.initial_equity
        bucket["challenger_return"] += (
            challenger_point.equity - challenger_previous
        ) / challenger.summary.initial_equity
        baseline_previous = point.equity
        challenger_previous = challenger_point.equity
    return result


def _lineage(
    test_start: datetime,
    test_end: datetime,
    *,
    discovery_start: datetime,
    frozen_at: datetime,
) -> str:
    if test_end <= discovery_start:
        return "PRE_DISCOVERY_HOLDOUT"
    if test_start > frozen_at:
        return "POST_FREEZE_FORWARD"
    if test_start >= discovery_start and test_end <= frozen_at:
        return "DISCOVERY_WINDOW_REUSE"
    return "BOUNDARY_CROSSING"


def _check(
    check_id: str,
    passed: bool,
    observed: Any,
    requirement: str,
    impact: str,
    recovery: str,
) -> dict[str, Any]:
    return {
        "id": check_id,
        "status": "PASS" if passed else "BLOCK",
        "observed": observed,
        "requirement": requirement,
        "impact": impact,
        "recovery_condition": recovery,
    }


def build_frozen_challenger_robustness(
    store: MarketStore,
    *,
    snapshot_id: str | None = None,
    settings: RobustnessSettings = RobustnessSettings(),
    observed_at: datetime | None = None,
) -> dict[str, Any]:
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
    symbols = tuple(str(item) for item in snapshot["symbols"])
    timeframe = str(snapshot["configuration"]["timeframe"])
    frozen_at = _utc(snapshot["as_of"])
    current = observed_at or datetime.now(timezone.utc)
    validation_as_of, per_asset_boundary = latest_synchronized_closed_boundary(
        store, symbols, timeframe, observed_at=current
    )
    if validation_as_of is None or validation_as_of < frozen_at:
        return _degraded("SYNCHRONIZED_VALIDATION_BOUNDARY_UNAVAILABLE", source_id)
    candles_by_symbol = {
        symbol: store.load_candles(symbol, timeframe, end=validation_as_of)
        for symbol in symbols
    }
    if len({len(candles) for candles in candles_by_symbol.values()}) != 1:
        return _degraded("UNALIGNED_VALIDATION_HISTORY", source_id)
    reference_times = tuple(
        candle.open_time for candle in next(iter(candles_by_symbol.values()))
    )
    if any(
        tuple(candle.open_time for candle in candles) != reference_times
        for candles in candles_by_symbol.values()
    ):
        return _degraded("UNALIGNED_VALIDATION_HISTORY", source_id)
    interval = timeframe_duration(timeframe)
    if any(
        right - left != interval
        for left, right in zip(reference_times, reference_times[1:])
    ):
        return _degraded("VALIDATION_HISTORY_GAP", source_id)
    weights = {
        str(symbol): float(weight)
        for symbol, weight in snapshot["portfolio"]["weights"].items()
    }
    funding_by_symbol = {
        symbol: store.load_funding_rates(
            symbol,
            start=candles_by_symbol[symbol][0].open_time,
            end=validation_as_of,
        )
        for symbol in symbols
    }
    spec = frozen_specification(source_id, frozen_at.isoformat())

    window_rows: list[dict[str, Any]] = []
    evaluated_window_sizes: set[int] = set()
    for window_id, requested_bars in settings.multi_windows:
        available = min(requested_bars, len(next(iter(candles_by_symbol.values()))))
        if available <= settings.warmup_bars or available in evaluated_window_sizes:
            continue
        evaluated_window_sizes.add(available)
        baseline: dict[str, ReplayResult] = {}
        challenger: dict[str, ReplayResult] = {}
        for symbol in symbols:
            candles = candles_by_symbol[symbol][-available:]
            baseline[symbol], challenger[symbol] = _run_pair(
                candles,
                funding_by_symbol[symbol],
                warmup_bars=settings.warmup_bars,
            )
        window_rows.append(
            {
                "window": window_id,
                "requested_bars": requested_bars,
                "evaluated_bars": available,
                "truncated": available < requested_bars,
                "spec_sha256": spec["spec_sha256"],
                **_comparison(baseline, challenger, weights),
            }
        )

    common_length = len(next(iter(candles_by_symbol.values())))
    # Anchor discovery lineage to the actual freeze boundary.  It must never
    # drift forward as new validation candles arrive.
    discovery_start = frozen_at - (
        timeframe_duration(timeframe) * settings.discovery_window_bars
    )
    fold_rows: list[dict[str, Any]] = []
    state_totals: dict[str, dict[str, float | int]] = defaultdict(
        lambda: {"bars": 0, "baseline_return": 0.0, "challenger_return": 0.0, "folds": 0}
    )
    test_start = settings.warmup_bars - 1
    fold_index = 0
    while test_start + settings.test_bars <= common_length:
        context_start = test_start - (settings.warmup_bars - 1)
        test_end = test_start + settings.test_bars
        baseline = {}
        challenger = {}
        fold_states: dict[str, dict[str, float | int]] = defaultdict(
            lambda: {"bars": 0, "baseline_return": 0.0, "challenger_return": 0.0}
        )
        for symbol in symbols:
            candles = candles_by_symbol[symbol][context_start:test_end]
            baseline[symbol], challenger[symbol] = _run_pair(
                candles,
                funding_by_symbol[symbol],
                warmup_bars=settings.warmup_bars,
            )
            for state, values in _state_attribution(
                baseline[symbol], challenger[symbol]
            ).items():
                fold_states[state]["bars"] += int(values["bars"])
                fold_states[state]["baseline_return"] += (
                    weights[symbol] * float(values["baseline_return"])
                )
                fold_states[state]["challenger_return"] += (
                    weights[symbol] * float(values["challenger_return"])
                )
        comparison = _comparison(baseline, challenger, weights)
        first = next(iter(candles_by_symbol.values()))
        start_at = first[test_start].open_time
        end_at = first[test_end - 1].open_time
        lineage = _lineage(
            start_at,
            end_at,
            discovery_start=discovery_start,
            frozen_at=frozen_at,
        )
        for state, values in fold_states.items():
            total = state_totals[state]
            total["bars"] += int(values["bars"])
            total["baseline_return"] += float(values["baseline_return"])
            total["challenger_return"] += float(values["challenger_return"])
            total["folds"] += 1
        fold_state_rows = sorted(
            (
                {
                    "market_state": state,
                    **values,
                    "return_delta": float(values["challenger_return"])
                    - float(values["baseline_return"]),
                }
                for state, values in fold_states.items()
            ),
            key=lambda item: item["market_state"],
        )
        fold_rows.append(
            {
                "fold_index": fold_index,
                "test_start_at": start_at.isoformat(),
                "test_end_at": end_at.isoformat(),
                "test_bars": settings.test_bars,
                "lineage": lineage,
                "selection_uses_fold": False,
                "spec_sha256": spec["spec_sha256"],
                "market_state_evidence": fold_state_rows,
                **comparison,
            }
        )
        fold_index += 1
        test_start += settings.step_bars

    lineage_summary = []
    for name in (
        "PRE_DISCOVERY_HOLDOUT",
        "DISCOVERY_WINDOW_REUSE",
        "POST_FREEZE_FORWARD",
        "BOUNDARY_CROSSING",
    ):
        group = [item for item in fold_rows if item["lineage"] == name]
        lineage_summary.append(
            {
                "lineage": name,
                "folds": len(group),
                "challenger_wins": sum(
                    item["deltas"]["total_return"] > 0 for item in group
                ),
                "win_rate": (
                    sum(item["deltas"]["total_return"] > 0 for item in group)
                    / len(group)
                    if group
                    else 0.0
                ),
                "mean_return_delta": (
                    fmean(item["deltas"]["total_return"] for item in group)
                    if group
                    else 0.0
                ),
            }
        )

    discovery_bars = min(settings.discovery_window_bars, common_length)
    stress_rows = []
    for scenario in STRESS_SCENARIOS:
        baseline = {}
        challenger = {}
        for symbol in symbols:
            baseline[symbol], challenger[symbol] = _run_pair(
                candles_by_symbol[symbol][-discovery_bars:],
                funding_by_symbol[symbol],
                warmup_bars=settings.warmup_bars,
                fee_multiplier=float(scenario["fee_multiplier"]),
                slippage_multiplier=float(scenario["slippage_multiplier"]),
                funding_multiplier=float(scenario["funding_multiplier"]),
            )
        stress_rows.append(
            {
                **scenario,
                "spec_sha256": spec["spec_sha256"],
                **_comparison(baseline, challenger, weights),
            }
        )

    state_rows = sorted([
        {
            "market_state": state,
            **values,
            "return_delta": float(values["challenger_return"])
            - float(values["baseline_return"]),
        }
        for state, values in sorted(state_totals.items())
    ], key=lambda item: (item["return_delta"], item["market_state"]))
    post = next(item for item in lineage_summary if item["lineage"] == "POST_FREEZE_FORWARD")
    holdout = next(item for item in lineage_summary if item["lineage"] == "PRE_DISCOVERY_HOLDOUT")
    window_win_rate = (
        sum(item["deltas"]["total_return"] > 0 for item in window_rows)
        / len(window_rows)
        if window_rows
        else 0.0
    )
    mean_turnover_reduction = (
        fmean(item["deltas"]["turnover_reduction"] for item in fold_rows)
        if fold_rows
        else 0.0
    )
    fold_win_rate = (
        sum(item["deltas"]["total_return"] > 0 for item in fold_rows)
        / len(fold_rows)
        if fold_rows
        else 0.0
    )
    weakest_fold = (
        min(fold_rows, key=lambda item: item["deltas"]["total_return"])
        if fold_rows
        else None
    )
    observed_states = [item for item in state_rows if item["bars"] > 0]
    positive_state_rate = (
        sum(item["return_delta"] >= 0 for item in observed_states)
        / len(observed_states)
        if observed_states
        else 0.0
    )
    stress_survives = all(
        item["deltas"]["total_return"] >= 0
        and item["challenger"]["liquidation_events"] == 0
        and item["deltas"]["max_drawdown"] <= 0.02
        for item in stress_rows
    )
    checks = [
        _check(
            "FROZEN_SPECIFICATION",
            all(item["spec_sha256"] == spec["spec_sha256"] for item in [*window_rows, *fold_rows, *stress_rows]),
            spec["spec_sha256"],
            "one unchanged hash across every evaluation",
            "Mixed parameters invalidate the robustness claim.",
            "Run again using only the frozen MIL-3.28 specification.",
        ),
        _check(
            "MULTI_WINDOW_CONSISTENCY",
            len(window_rows) >= 3 and window_win_rate >= 0.75,
            window_win_rate,
            ">= 75% positive windows across at least 3 windows",
            "A single-window effect is exposed to period selection.",
            "Accumulate consistent fixed-policy results without retuning.",
        ),
        _check(
            "PRE_DISCOVERY_HOLDOUT",
            holdout["folds"] >= 3 and holdout["win_rate"] >= 0.50,
            holdout,
            ">= 3 folds and >= 50% win rate",
            "Insufficient holdout performance leaves discovery-window overfit unresolved.",
            "Acquire additional independent historical data; do not alter the specification.",
        ),
        _check(
            "POST_FREEZE_FORWARD_EVIDENCE",
            post["folds"] >= settings.min_post_freeze_folds and post["win_rate"] >= 0.50,
            post,
            f">= {settings.min_post_freeze_folds} folds and >= 50% win rate",
            "Without post-freeze evidence, retrospective validation cannot establish persistence.",
            "Keep the parameters frozen and collect new fully closed weekly folds.",
        ),
        _check(
            "MARKET_STATE_BREADTH",
            len(observed_states) >= 5 and positive_state_rate >= 0.50,
            {"observed_states": len(observed_states), "positive_state_rate": positive_state_rate},
            ">= 5 observed states and >= 50% non-negative state deltas",
            "Narrow state coverage can hide regime-specific failure.",
            "Collect fixed-policy evidence spanning additional market states.",
        ),
        _check(
            "STRESSED_COST_SURVIVAL",
            stress_survives,
            sum(item["deltas"]["total_return"] >= 0 for item in stress_rows),
            "all scenarios non-negative delta, drawdown delta <= 2 points, zero liquidation events",
            "Cost stress failure would make the improvement fragile to execution assumptions.",
            "Continue observation under the fixed specification; do not weaken stress assumptions.",
        ),
        _check(
            "ROLLING_FOLD_CONSISTENCY",
            len(fold_rows) >= 8
            and fold_win_rate >= 0.60
            and weakest_fold is not None
            and weakest_fold["deltas"]["total_return"] >= -0.05,
            {
                "folds": len(fold_rows),
                "win_rate": fold_win_rate,
                "weakest_return_delta": (
                    weakest_fold["deltas"]["total_return"] if weakest_fold else None
                ),
            },
            ">= 8 folds, >= 60% positive, weakest return delta >= -5 points",
            "Weak or concentrated rolling results expose period dependence.",
            "Collect additional fixed-policy folds; do not retune against the weakest fold.",
        ),
        _check(
            "ROLLING_TURNOVER_REDUCTION",
            mean_turnover_reduction >= 0.50,
            mean_turnover_reduction,
            ">= 50% mean rolling-fold reduction",
            "Weak rolling reduction would contradict the challenger's stated purpose.",
            "Continue fixed-policy evidence collection without parameter tuning.",
        ),
    ]
    blocking = [item["id"] for item in checks if item["status"] == "BLOCK"]
    material_adverse = any(
        item["deltas"]["total_return"] < -0.05
        or item["challenger"]["liquidation_events"] > 0
        for item in stress_rows
    )
    non_forward_blocking = [
        item for item in blocking if item != "POST_FREEZE_FORWARD_EVIDENCE"
    ]
    disposition = (
        "REJECT_FROZEN_CHALLENGER"
        if material_adverse
        else "WAIT_FOR_POST_FREEZE_EVIDENCE"
        if not non_forward_blocking and "POST_FREEZE_FORWARD_EVIDENCE" in blocking
        else "ROBUSTNESS_CANDIDATE"
        if not blocking
        else "CONTINUE_FIXED_VALIDATION"
    )
    overfit_level = (
        "HIGH" if post["folds"] == 0 else "ELEVATED" if post["folds"] < settings.min_post_freeze_folds else "CONTROLLED"
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "execution_mode": EXECUTION_MODE,
        "status": "READY",
        "generated_at": _utc(current).isoformat(),
        "data_trust": {
            **diagnostic["data_trust"],
            "validation_as_of": validation_as_of.isoformat(),
            "per_asset_closed_boundary": {
                symbol: boundary.isoformat() if boundary else None
                for symbol, boundary in per_asset_boundary.items()
            },
            "fully_closed": True,
        },
        "authority": _authority(),
        "frozen_specification": spec,
        "validation_design": {
            "selection_uses_any_validation_fold": False,
            "parameter_search_count": 0,
            "warmup_bars": settings.warmup_bars,
            "test_bars": settings.test_bars,
            "step_bars": settings.step_bars,
            "discovery_window_bars": settings.discovery_window_bars,
            "discovery_start_at": discovery_start.isoformat(),
            "frozen_at": frozen_at.isoformat(),
            "lineage_meanings": {
                "PRE_DISCOVERY_HOLDOUT": "not used in the MIL-3.28 discovery window",
                "DISCOVERY_WINDOW_REUSE": "retrospective reuse; not independent evidence",
                "POST_FREEZE_FORWARD": "new fully closed evidence after parameter freeze",
                "BOUNDARY_CROSSING": "mixed lineage; excluded from independent claims",
            },
        },
        "multi_window": window_rows,
        "walk_forward": {
            "folds": fold_rows,
            "lineage_summary": lineage_summary,
            "fold_count": len(fold_rows),
            "win_rate": fold_win_rate,
            "weakest_fold": weakest_fold,
            "mean_turnover_reduction": mean_turnover_reduction,
        },
        "market_state_evidence": state_rows,
        "stress_matrix": stress_rows,
        "overfit_assessment": {
            "level": overfit_level,
            "post_freeze_folds": post["folds"],
            "discovery_reuse_folds": next(
                item["folds"] for item in lineage_summary
                if item["lineage"] == "DISCOVERY_WINDOW_REUSE"
            ),
            "reason": (
                "No complete post-freeze forward folds are available."
                if post["folds"] == 0
                else "Post-freeze evidence remains below the minimum."
                if post["folds"] < settings.min_post_freeze_folds
                else "Minimum post-freeze fold evidence is available."
            ),
        },
        "review_gate": {
            "disposition": disposition,
            "checks": checks,
            "blocking_checks": blocking,
            "requires_human_review": True,
            "parameter_tuning_allowed": False,
            "proposal_creation_allowed": False,
            "challenger_activation_allowed": False,
            "live_execution_allowed": False,
        },
    }
