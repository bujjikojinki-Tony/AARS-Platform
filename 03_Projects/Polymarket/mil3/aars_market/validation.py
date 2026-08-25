from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from itertools import product
from statistics import fmean
from typing import Callable, Sequence

from .models import Candle, FundingRate
from .simulation import (
    AarsDynamicStrategy,
    BuyAndHoldStrategy,
    LeveragedFuturesLongGridStrategy,
    ReplayEngine,
    ShadowStrategy,
    SimulationSummary,
    SpotGridStrategy,
)


EXECUTION_MODE = "PAPER_ONLY"
SUPPORTED_TARGETS = ("AARS_DYNAMIC", "SPOT_GRID", "FUTURES_LONG_GRID")


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


@dataclass(frozen=True)
class ValidationCandidate:
    target_strategy: str
    aars_max_abs_exposure: float = 1.0
    futures_leverage: float = 10.0
    grid_spacing_pct: float = 0.01
    grid_levels: int = 5
    tactical_hedge: bool = True

    def __post_init__(self) -> None:
        if self.target_strategy not in (*SUPPORTED_TARGETS, "BUY_HOLD"):
            raise ValueError(f"unsupported target strategy: {self.target_strategy}")
        if self.aars_max_abs_exposure <= 0 or self.futures_leverage <= 0:
            raise ValueError("exposure and leverage must be positive")
        if self.grid_spacing_pct <= 0 or self.grid_levels <= 0:
            raise ValueError("grid spacing and levels must be positive")

    @property
    def candidate_id(self) -> str:
        if self.target_strategy == "AARS_DYNAMIC":
            return f"AARS_DYNAMIC:exposure={self.aars_max_abs_exposure:g}"
        if self.target_strategy == "SPOT_GRID":
            return f"SPOT_GRID:spacing={self.grid_spacing_pct:g}:levels={self.grid_levels}"
        if self.target_strategy == "FUTURES_LONG_GRID":
            hedge = "on" if self.tactical_hedge else "off"
            return (
                f"FUTURES_LONG_GRID:leverage={self.futures_leverage:g}:"
                f"spacing={self.grid_spacing_pct:g}:levels={self.grid_levels}:hedge={hedge}"
            )
        return "BUY_HOLD"

    def as_dict(self) -> dict[str, object]:
        return {"candidate_id": self.candidate_id, **asdict(self)}


@dataclass(frozen=True)
class ValidationSettings:
    warmup_bars: int = 120
    initial_equity: float = 1000.0
    fee_rate: float = 0.0005
    slippage_rate: float = 0.0002
    funding_rate_per_bar: float = 0.0
    funding_rates: tuple[FundingRate, ...] = ()
    maintenance_margin_rate: float = 0.005

    def __post_init__(self) -> None:
        if self.warmup_bars < 60:
            raise ValueError("warmup_bars must be at least 60")
        if self.initial_equity <= 0:
            raise ValueError("initial_equity must be positive")


@dataclass(frozen=True)
class FoldWindow:
    fold_index: int
    train_context_start: int
    train_start: int
    train_end: int
    test_context_start: int
    test_start: int
    test_end: int

    def as_dict(self, candles: Sequence[Candle]) -> dict[str, object]:
        return {
            **asdict(self),
            "train_start_at": candles[self.train_start].open_time.isoformat(),
            "train_end_at": candles[self.train_end - 1].open_time.isoformat(),
            "test_start_at": candles[self.test_start].open_time.isoformat(),
            "test_end_at": candles[self.test_end - 1].open_time.isoformat(),
            "train_bars": self.train_end - self.train_start,
            "test_bars": self.test_end - self.test_start,
        }


@dataclass(frozen=True)
class CandidateScore:
    candidate: ValidationCandidate
    score: float
    summary: SimulationSummary


@dataclass(frozen=True)
class FoldResult:
    window: FoldWindow
    selected: ValidationCandidate
    training_score: float
    training_summary: SimulationSummary
    test_score: float
    test_summary: SimulationSummary
    baseline_summary: SimulationSummary
    regime: str
    training_ranking: tuple[CandidateScore, ...]


Evaluator = Callable[
    [Sequence[Candle], ValidationCandidate, ValidationSettings], SimulationSummary
]


def build_candidates(
    target_strategy: str,
    *,
    aars_exposures: Sequence[float] = (0.25, 0.5, 0.75, 1.0),
    futures_leverages: Sequence[float] = (2.0, 5.0, 10.0),
    grid_spacings: Sequence[float] = (0.005, 0.01, 0.02),
    grid_levels: Sequence[int] = (3, 5),
    tactical_hedges: Sequence[bool] = (True, False),
    candidate_cap: int = 64,
) -> tuple[ValidationCandidate, ...]:
    target = target_strategy.upper()
    if target not in SUPPORTED_TARGETS:
        raise ValueError(f"unsupported target strategy: {target}")
    if candidate_cap <= 0:
        raise ValueError("candidate_cap must be positive")
    if target == "AARS_DYNAMIC":
        candidates = [
            ValidationCandidate(target, aars_max_abs_exposure=value)
            for value in sorted(set(aars_exposures))
        ]
    elif target == "SPOT_GRID":
        candidates = [
            ValidationCandidate(target, grid_spacing_pct=spacing, grid_levels=levels)
            for spacing, levels in product(
                sorted(set(grid_spacings)), sorted(set(grid_levels))
            )
        ]
    else:
        candidates = [
            ValidationCandidate(
                target,
                futures_leverage=leverage,
                grid_spacing_pct=spacing,
                grid_levels=levels,
                tactical_hedge=hedge,
            )
            for leverage, spacing, levels, hedge in product(
                sorted(set(futures_leverages)),
                sorted(set(grid_spacings)),
                sorted(set(grid_levels)),
                sorted(set(tactical_hedges), reverse=True),
            )
        ]
    if not candidates:
        raise ValueError("parameter grid produced no candidates")
    if len(candidates) > candidate_cap:
        raise ValueError(
            f"parameter grid has {len(candidates)} candidates; cap={candidate_cap}"
        )
    return tuple(candidates)


def build_walk_forward_folds(
    candles: Sequence[Candle],
    *,
    warmup_bars: int,
    train_bars: int,
    test_bars: int,
    step_bars: int | None = None,
) -> tuple[FoldWindow, ...]:
    if warmup_bars < 60 or train_bars <= 0 or test_bars <= 0:
        raise ValueError("warmup must be >= 60 and train/test bars must be positive")
    step = test_bars if step_bars is None else step_bars
    if step <= 0:
        raise ValueError("step_bars must be positive")
    folds: list[FoldWindow] = []
    offset = 0
    required = warmup_bars - 1 + train_bars + test_bars
    while offset + required <= len(candles):
        train_start = offset + warmup_bars - 1
        train_end = train_start + train_bars
        test_start = train_end
        test_end = test_start + test_bars
        folds.append(
            FoldWindow(
                fold_index=len(folds),
                train_context_start=offset,
                train_start=train_start,
                train_end=train_end,
                test_context_start=test_start - (warmup_bars - 1),
                test_start=test_start,
                test_end=test_end,
            )
        )
        offset += step
    return tuple(folds)


def _strategy(candidate: ValidationCandidate) -> ShadowStrategy:
    if candidate.target_strategy == "AARS_DYNAMIC":
        return AarsDynamicStrategy(max_abs_exposure=candidate.aars_max_abs_exposure)
    if candidate.target_strategy == "SPOT_GRID":
        return SpotGridStrategy(
            spacing_pct=candidate.grid_spacing_pct, levels=candidate.grid_levels
        )
    if candidate.target_strategy == "FUTURES_LONG_GRID":
        return LeveragedFuturesLongGridStrategy(
            max_leverage=candidate.futures_leverage,
            spacing_pct=candidate.grid_spacing_pct,
            levels=candidate.grid_levels,
            tactical_hedge=candidate.tactical_hedge,
        )
    return BuyAndHoldStrategy()


def evaluate_candidate(
    candles: Sequence[Candle],
    candidate: ValidationCandidate,
    settings: ValidationSettings,
) -> SimulationSummary:
    engine = ReplayEngine(
        initial_equity=settings.initial_equity,
        fee_rate=settings.fee_rate,
        slippage_rate=settings.slippage_rate,
        funding_rate_per_bar=settings.funding_rate_per_bar,
        funding_rates=settings.funding_rates,
        maintenance_margin_rate=settings.maintenance_margin_rate,
    )
    return engine.run(candles, _strategy(candidate), warmup_bars=settings.warmup_bars)


def risk_adjusted_score(summary: SimulationSummary) -> float:
    sharpe = max(-5.0, min(5.0, summary.sharpe_approx))
    sortino = max(-5.0, min(5.0, summary.sortino))
    return (
        sharpe
        + 0.5 * sortino
        + summary.total_return
        - 2.0 * summary.max_drawdown
        - 2.0 * summary.max_liquidation_risk
        - 10.0 * summary.liquidation_events
    )


def _regime(candles: Sequence[Candle], window: FoldWindow, threshold: float) -> str:
    start = candles[window.test_start].close
    end = candles[window.test_end - 1].close
    change = end / start - 1.0
    if change >= threshold:
        return "UPTREND"
    if change <= -threshold:
        return "DOWNTREND"
    return "RANGE"


def _summary_payload(summary: SimulationSummary) -> dict[str, object]:
    payload: dict[str, object] = {}
    for key, value in summary.as_dict().items():
        payload[key] = None if isinstance(value, float) and not math.isfinite(value) else value
    if summary.profit_factor == float("inf"):
        payload["profit_factor_display"] = "INF"
    return payload


def _mean(values: Sequence[float]) -> float:
    return fmean(values) if values else 0.0


def walk_forward_validate(
    candles: Sequence[Candle],
    candidates: Sequence[ValidationCandidate],
    *,
    train_bars: int,
    test_bars: int,
    settings: ValidationSettings = ValidationSettings(),
    step_bars: int | None = None,
    regime_threshold: float = 0.05,
    evaluator: Evaluator = evaluate_candidate,
    generated_at: datetime | None = None,
) -> dict[str, object]:
    if not candles:
        raise ValueError("candles are required")
    symbols = {item.symbol.upper() for item in candles}
    timeframes = {item.timeframe for item in candles}
    if len(symbols) != 1 or len(timeframes) != 1:
        raise ValueError("candles must share one symbol and timeframe")
    if any(left.open_time >= right.open_time for left, right in zip(candles, candles[1:])):
        raise ValueError("candles must be strictly chronological")
    if not candidates:
        raise ValueError("at least one validation candidate is required")
    targets = {item.target_strategy for item in candidates}
    if len(targets) != 1 or "BUY_HOLD" in targets:
        raise ValueError("candidates must share one non-baseline target strategy")
    if regime_threshold <= 0:
        raise ValueError("regime_threshold must be positive")
    folds = build_walk_forward_folds(
        candles,
        warmup_bars=settings.warmup_bars,
        train_bars=train_bars,
        test_bars=test_bars,
        step_bars=step_bars,
    )
    if not folds:
        required = settings.warmup_bars - 1 + train_bars + test_bars
        raise ValueError(f"insufficient candles for one fold: need={required} stored={len(candles)}")

    baseline = ValidationCandidate("BUY_HOLD")
    results: list[FoldResult] = []
    sensitivity: dict[str, list[float]] = {item.candidate_id: [] for item in candidates}
    for window in folds:
        train_slice = candles[window.train_context_start : window.train_end]
        ranked: list[CandidateScore] = []
        for candidate in candidates:
            summary = evaluator(train_slice, candidate, settings)
            score = risk_adjusted_score(summary)
            sensitivity[candidate.candidate_id].append(score)
            ranked.append(CandidateScore(candidate, score, summary))
        ranked.sort(key=lambda item: (-item.score, item.candidate.candidate_id))
        selected = ranked[0]
        test_slice = candles[window.test_context_start : window.test_end]
        test_summary = evaluator(test_slice, selected.candidate, settings)
        baseline_summary = evaluator(test_slice, baseline, settings)
        results.append(
            FoldResult(
                window=window,
                selected=selected.candidate,
                training_score=selected.score,
                training_summary=selected.summary,
                test_score=risk_adjusted_score(test_summary),
                test_summary=test_summary,
                baseline_summary=baseline_summary,
                regime=_regime(candles, window, regime_threshold),
                training_ranking=tuple(ranked),
            )
        )

    selection_counts = {
        candidate.candidate_id: sum(result.selected == candidate for result in results)
        for candidate in candidates
    }
    most_selected = max(selection_counts.values())
    selection_stability = most_selected / len(results)
    train_scores = [item.training_score for item in results]
    test_scores = [item.test_score for item in results]
    score_decay = _mean(train_scores) - _mean(test_scores)
    beat_baseline = sum(
        item.test_summary.total_return > item.baseline_summary.total_return
        for item in results
    )
    warnings: list[dict[str, str]] = []
    if len(results) < 3:
        warnings.append(
            {"code": "INSUFFICIENT_FOLDS", "severity": "HIGH", "detail": "fewer than 3 complete chronological folds"}
        )
    if len(candidates) == 1:
        warnings.append(
            {"code": "NO_PARAMETER_SENSITIVITY", "severity": "MEDIUM", "detail": "only one candidate was evaluated"}
        )
    effective_step = test_bars if step_bars is None else step_bars
    if effective_step < test_bars:
        warnings.append(
            {"code": "OVERLAPPING_TEST_WINDOWS", "severity": "MEDIUM", "detail": "test periods overlap and fold counts are not independent"}
        )
    if selection_stability < 0.60:
        warnings.append(
            {"code": "PARAMETER_INSTABILITY", "severity": "MEDIUM", "detail": "no candidate was selected in 60% of folds"}
        )
    if score_decay > 1.0 or (_mean(train_scores) > 0 and _mean(test_scores) < 0):
        warnings.append(
            {"code": "TRAIN_TEST_SCORE_DECAY", "severity": "HIGH", "detail": "out-of-sample risk-adjusted score materially decayed"}
        )
    if beat_baseline * 2 < len(results):
        warnings.append(
            {"code": "BASELINE_UNDERPERFORMANCE", "severity": "HIGH", "detail": "selected strategy beat Buy & Hold in fewer than half of folds"}
        )
    if any(item.test_summary.liquidation_events for item in results):
        warnings.append(
            {"code": "LIQUIDATION_APPROXIMATION_BREACH", "severity": "HIGH", "detail": "one or more test folds breached the liquidation approximation"}
        )
    if next(iter(targets)) in ("AARS_DYNAMIC", "FUTURES_LONG_GRID") and not settings.funding_rates:
        warnings.append(
            {"code": "FUNDING_HISTORY_FALLBACK", "severity": "HIGH", "detail": "timestamped funding history is absent; validation used the explicit per-bar fallback"}
        )

    regime_names = sorted({item.regime for item in results})
    regime_evidence = [
        {
            "regime": regime,
            "folds": len(group := [item for item in results if item.regime == regime]),
            "mean_test_return": _mean([item.test_summary.total_return for item in group]),
            "mean_baseline_return": _mean([item.baseline_summary.total_return for item in group]),
            "max_test_drawdown": max(item.test_summary.max_drawdown for item in group),
        }
        for regime in regime_names
    ]
    fold_payloads = []
    for item in results:
        fold_payloads.append(
            {
                "window": item.window.as_dict(candles),
                "selected_candidate": item.selected.as_dict(),
                "regime": item.regime,
                "training_score": item.training_score,
                "test_score": item.test_score,
                "test_excess_return_vs_buy_hold": (
                    item.test_summary.total_return - item.baseline_summary.total_return
                ),
                "training_summary": _summary_payload(item.training_summary),
                "test_summary": _summary_payload(item.test_summary),
                "buy_hold_test_summary": _summary_payload(item.baseline_summary),
                "training_ranking": [
                    {
                        "rank": rank,
                        "candidate": scored.candidate.as_dict(),
                        "score": scored.score,
                    }
                    for rank, scored in enumerate(item.training_ranking, start=1)
                ],
            }
        )
    created = _utc(generated_at or datetime.now(timezone.utc))
    return {
        "schema_version": "mil3.robustness-validation.v1",
        "execution_mode": EXECUTION_MODE,
        "generated_at": created.isoformat(),
        "market": {
            "symbol": candles[-1].symbol,
            "timeframe": candles[-1].timeframe,
            "stored_bars": len(candles),
        },
        "target_strategy": next(iter(targets)),
        "selection_policy": {
            "uses_test_for_selection": False,
            "score": "clamped_sharpe + 0.5*clamped_sortino + return - 2*drawdown - 2*liquidation_risk - 10*liquidation_events",
            "tie_break": "candidate_id ascending",
            "warmup_bars": settings.warmup_bars,
            "train_bars": train_bars,
            "test_bars": test_bars,
            "step_bars": test_bars if step_bars is None else step_bars,
        },
        "candidates": [item.as_dict() for item in candidates],
        "folds": fold_payloads,
        "sensitivity": [
            {
                "candidate": candidate.as_dict(),
                "selection_count": selection_counts[candidate.candidate_id],
                "mean_training_score": _mean(sensitivity[candidate.candidate_id]),
                "min_training_score": min(sensitivity[candidate.candidate_id]),
                "max_training_score": max(sensitivity[candidate.candidate_id]),
            }
            for candidate in candidates
        ],
        "regime_evidence": regime_evidence,
        "aggregate": {
            "folds": len(results),
            "mean_training_score": _mean(train_scores),
            "mean_test_score": _mean(test_scores),
            "train_test_score_decay": score_decay,
            "mean_test_return": _mean([item.test_summary.total_return for item in results]),
            "mean_buy_hold_return": _mean([item.baseline_summary.total_return for item in results]),
            "max_test_drawdown": max(item.test_summary.max_drawdown for item in results),
            "max_test_liquidation_risk": max(item.test_summary.max_liquidation_risk for item in results),
            "test_liquidation_events": sum(item.test_summary.liquidation_events for item in results),
            "profitable_test_folds": sum(item.test_summary.total_return > 0 for item in results),
            "beat_buy_hold_folds": beat_baseline,
            "selection_stability": selection_stability,
        },
        "warnings": warnings,
        "review_gate": {
            "disposition": "DEFER" if any(item["severity"] == "HIGH" for item in warnings) else "READY_FOR_SHADOW_REVIEW",
            "live_execution_allowed": False,
        },
    }


def write_validation_report(path: str, payload: dict[str, object]) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")


def combine_validation_reports(
    reports: Sequence[dict[str, object]],
    *,
    generated_at: datetime | None = None,
) -> dict[str, object]:
    if not reports:
        raise ValueError("at least one validation report is required")
    if any(item.get("execution_mode") != EXECUTION_MODE for item in reports):
        raise ValueError("all validation reports must be PAPER_ONLY")
    targets = {str(item["target_strategy"]) for item in reports}
    if len(targets) != 1:
        raise ValueError("all validation reports must share one target strategy")
    symbols = [str(item["market"]["symbol"]) for item in reports]  # type: ignore[index]
    if len(set(symbols)) != len(symbols):
        raise ValueError("validation report symbols must be unique")
    aggregates = [item["aggregate"] for item in reports]
    total_folds = sum(int(item["folds"]) for item in aggregates)  # type: ignore[index]
    beat_folds = sum(int(item["beat_buy_hold_folds"]) for item in aggregates)  # type: ignore[index]
    warnings = sorted(
        {
            str(warning["code"])
            for report in reports
            for warning in report["warnings"]  # type: ignore[union-attr]
        }
    )
    deferred = [
        symbol
        for symbol, report in zip(symbols, reports)
        if report["review_gate"]["disposition"] == "DEFER"  # type: ignore[index]
    ]
    created = _utc(generated_at or datetime.now(timezone.utc))
    return {
        "schema_version": "mil3.robustness-validation-batch.v1",
        "execution_mode": EXECUTION_MODE,
        "generated_at": created.isoformat(),
        "target_strategy": next(iter(targets)),
        "markets": reports,
        "aggregate": {
            "assets": len(reports),
            "symbols": symbols,
            "total_folds": total_folds,
            "mean_asset_test_return": _mean(
                [float(item["mean_test_return"]) for item in aggregates]  # type: ignore[index]
            ),
            "mean_asset_buy_hold_return": _mean(
                [float(item["mean_buy_hold_return"]) for item in aggregates]  # type: ignore[index]
            ),
            "beat_buy_hold_folds": beat_folds,
            "beat_buy_hold_ratio": beat_folds / total_folds if total_folds else 0.0,
            "max_test_drawdown": max(
                float(item["max_test_drawdown"]) for item in aggregates  # type: ignore[index]
            ),
            "max_test_liquidation_risk": max(
                float(item["max_test_liquidation_risk"]) for item in aggregates  # type: ignore[index]
            ),
            "deferred_assets": deferred,
            "warning_codes": warnings,
        },
        "review_gate": {
            "disposition": "DEFER" if deferred else "READY_FOR_SHADOW_REVIEW",
            "live_execution_allowed": False,
        },
    }
