from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from statistics import fmean
from typing import Any, Sequence

from .service import DEFAULT_SYMBOLS, DashboardService, PortfolioRequest
from .storage import MarketStore
from .validation import (
    ValidationCandidate,
    ValidationSettings,
    combine_validation_reports,
    walk_forward_validate,
)


EXECUTION_MODE = "PAPER_ONLY"
SNAPSHOT_SCHEMA_VERSION = "mil3.shadow-daily.v1"
STABILITY_SCHEMA_VERSION = "mil3.shadow-stability.v1"


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def build_shadow_daily_snapshot(
    store: MarketStore,
    candidates: Sequence[ValidationCandidate],
    *,
    symbols: Sequence[str] = DEFAULT_SYMBOLS,
    timeframe: str = "1h",
    replay_window: str = "90d",
    portfolio_strategy: str = "AARS_DYNAMIC",
    train_bars: int = 720,
    test_bars: int = 168,
    step_bars: int | None = None,
    settings: ValidationSettings = ValidationSettings(),
    now: datetime | None = None,
) -> dict[str, Any]:
    """Build one non-mutating, multi-asset daily shadow evidence bundle."""
    normalized = tuple(dict.fromkeys(symbol.upper() for symbol in symbols))
    if not normalized:
        raise ValueError("shadow symbols must not be empty")
    if len(normalized) != len(tuple(symbols)):
        raise ValueError("shadow symbols must be unique")
    if not candidates:
        raise ValueError("validation candidates are required")
    targets = {candidate.target_strategy for candidate in candidates}
    if len(targets) != 1:
        raise ValueError("validation candidates must share one target strategy")

    generated = _utc(now or datetime.now(timezone.utc))
    reports: list[dict[str, object]] = []
    evidence_times: dict[str, str] = {}
    for symbol in normalized:
        candles = store.load_candles(symbol, timeframe)
        if not candles:
            raise ValueError(f"no candles stored for {symbol} {timeframe}")
        funding = store.load_funding_rates(
            symbol, start=candles[0].open_time, end=candles[-1].open_time
        )
        reports.append(
            walk_forward_validate(
                candles,
                candidates,
                train_bars=train_bars,
                test_bars=test_bars,
                step_bars=step_bars,
                settings=ValidationSettings(
                    warmup_bars=settings.warmup_bars,
                    initial_equity=settings.initial_equity,
                    fee_rate=settings.fee_rate,
                    slippage_rate=settings.slippage_rate,
                    funding_rate_per_bar=settings.funding_rate_per_bar,
                    funding_rates=tuple(funding),
                    maintenance_margin_rate=settings.maintenance_margin_rate,
                ),
                generated_at=generated,
            )
        )
        evidence_times[symbol] = _utc(candles[-1].open_time).isoformat()

    validation = combine_validation_reports(reports, generated_at=generated)
    portfolio = DashboardService(store, warmup_bars=settings.warmup_bars).build_portfolio(
        PortfolioRequest(
            symbols=normalized,
            timeframe=timeframe,
            replay_window=replay_window,
            strategy=portfolio_strategy,
        ),
        now=generated,
    )
    deferred = (
        validation["review_gate"]["disposition"] == "DEFER"
        or portfolio["review_gate"]["disposition"] == "DEFER"
    )
    reasons: list[str] = []
    if validation["review_gate"]["disposition"] == "DEFER":
        reasons.append("VALIDATION_DEFERRED")
    if portfolio["review_gate"]["disposition"] == "DEFER":
        reasons.append("PORTFOLIO_DEGRADED")

    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "execution_mode": EXECUTION_MODE,
        "generated_at": generated.isoformat(),
        # The oldest latest candle is the last synchronized evidence boundary.
        "as_of": min(evidence_times.values()),
        "symbols": list(normalized),
        "evidence_as_of": evidence_times,
        "configuration": {
            "validation_strategy": next(iter(targets)),
            "portfolio_strategy": portfolio_strategy,
            "timeframe": timeframe,
            "replay_window": replay_window,
            "warmup_bars": settings.warmup_bars,
            "train_bars": train_bars,
            "test_bars": test_bars,
            "step_bars": test_bars if step_bars is None else step_bars,
            "candidate_ids": [candidate.candidate_id for candidate in candidates],
            "portfolio_parameter_policy": "fixed_existing_strategy_defaults",
        },
        "validation": validation,
        "portfolio": portfolio,
        "review_gate": {
            "disposition": "DEFER" if deferred else "READY_FOR_SHADOW_REVIEW",
            "reasons": reasons,
            "live_execution_allowed": False,
        },
    }


def _markets(validation: dict[str, Any]) -> list[dict[str, Any]]:
    if "markets" in validation:
        return list(validation["markets"])
    return [validation]


def _warning_codes(validation: dict[str, Any]) -> list[str]:
    return sorted(
        {
            str(warning["code"])
            for market in _markets(validation)
            for warning in market.get("warnings", [])
        }
    )


def _selected_candidates(validation: dict[str, Any]) -> dict[str, str]:
    selected: dict[str, str] = {}
    for market in _markets(validation):
        folds = market.get("folds", [])
        if folds:
            selected[str(market["market"]["symbol"])] = str(
                folds[-1]["selected_candidate"]["candidate_id"]
            )
    return selected


def _point(snapshot_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    validation = payload["validation"]
    aggregates = [market["aggregate"] for market in _markets(validation)]
    portfolio = payload["portfolio"]["summary"]
    return {
        "snapshot_id": snapshot_id,
        "as_of": payload["as_of"],
        "validation_strategy": payload["configuration"]["validation_strategy"],
        "portfolio_strategy": payload["configuration"]["portfolio_strategy"],
        "selected_candidates": _selected_candidates(validation),
        "warning_codes": _warning_codes(validation),
        "mean_validation_test_return": fmean(
            float(item["mean_test_return"]) for item in aggregates
        ),
        "mean_selection_stability": fmean(
            float(item["selection_stability"]) for item in aggregates
        ),
        "portfolio": {
            key: portfolio[key]
            for key in (
                "total_return",
                "max_drawdown",
                "final_net_exposure",
                "final_gross_exposure",
                "final_effective_leverage",
                "min_margin_buffer_pct",
                "max_liquidation_risk",
                "liquidation_events",
                "degraded",
            )
        },
        "review_disposition": payload["review_gate"]["disposition"],
    }


def build_shadow_stability(
    snapshots: Sequence[tuple[str, dict[str, Any]]],
    *,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    """Derive deterministic parameter, warning, risk, and review transitions."""
    points = [_point(snapshot_id, payload) for snapshot_id, payload in snapshots]
    transitions: list[dict[str, Any]] = []
    warning_counts: Counter[str] = Counter()
    consecutive_ready = 0
    for point in points:
        warning_counts.update(point["warning_codes"])
        if point["review_disposition"] == "READY_FOR_SHADOW_REVIEW":
            consecutive_ready += 1
        else:
            consecutive_ready = 0

    for before, after in zip(points, points[1:]):
        symbols = sorted(
            set(before["selected_candidates"]) | set(after["selected_candidates"])
        )
        candidate_changes = [
            {
                "symbol": symbol,
                "before": before["selected_candidates"].get(symbol),
                "after": after["selected_candidates"].get(symbol),
            }
            for symbol in symbols
            if before["selected_candidates"].get(symbol)
            != after["selected_candidates"].get(symbol)
        ]
        before_warnings = set(before["warning_codes"])
        after_warnings = set(after["warning_codes"])
        transitions.append(
            {
                "from_snapshot_id": before["snapshot_id"],
                "to_snapshot_id": after["snapshot_id"],
                "candidate_changes": candidate_changes,
                "warnings_added": sorted(after_warnings - before_warnings),
                "warnings_resolved": sorted(before_warnings - after_warnings),
                "validation_return_delta": (
                    after["mean_validation_test_return"]
                    - before["mean_validation_test_return"]
                ),
                "portfolio_return_delta": (
                    after["portfolio"]["total_return"]
                    - before["portfolio"]["total_return"]
                ),
                "portfolio_drawdown_delta": (
                    after["portfolio"]["max_drawdown"]
                    - before["portfolio"]["max_drawdown"]
                ),
                "liquidation_risk_delta": (
                    after["portfolio"]["max_liquidation_risk"]
                    - before["portfolio"]["max_liquidation_risk"]
                ),
                "review_transition": (
                    None
                    if before["review_disposition"] == after["review_disposition"]
                    else {
                        "before": before["review_disposition"],
                        "after": after["review_disposition"],
                    }
                ),
            }
        )

    parameter_change_events = sum(
        bool(transition["candidate_changes"]) for transition in transitions
    )
    history_warnings: list[str] = []
    if len(points) < 7:
        history_warnings.append("INSUFFICIENT_DAILY_HISTORY")
    if transitions and parameter_change_events / len(transitions) > 0.5:
        history_warnings.append("PARAMETER_CHURN")
    generated = _utc(generated_at or datetime.now(timezone.utc))
    return {
        "schema_version": STABILITY_SCHEMA_VERSION,
        "execution_mode": EXECUTION_MODE,
        "generated_at": generated.isoformat(),
        "snapshot_count": len(points),
        "points": points,
        "transitions": transitions,
        "summary": {
            "current_disposition": points[-1]["review_disposition"] if points else None,
            "consecutive_ready_snapshots": consecutive_ready,
            "parameter_change_events": parameter_change_events,
            "recurring_warning_counts": dict(sorted(warning_counts.items())),
            "history_warnings": history_warnings,
        },
        "review_gate": {
            "disposition": (
                points[-1]["review_disposition"] if points else "DEFER"
            ),
            "live_execution_allowed": False,
        },
    }
