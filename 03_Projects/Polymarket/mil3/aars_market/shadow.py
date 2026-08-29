from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
from statistics import fmean
from typing import Any, Sequence

from .runtime_ledger import (
    latest_synchronized_closed_boundary,
    timeframe_duration,
)
from .service import DEFAULT_SYMBOLS, DashboardService, PortfolioRequest
from .storage import MarketStore
from .validation import (
    ValidationCandidate,
    ValidationSettings,
    combine_validation_reports,
    walk_forward_validate,
)


EXECUTION_MODE = "PAPER_ONLY"
SNAPSHOT_SCHEMA_VERSION = "mil3.shadow-daily.v2"
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
    synchronized, per_asset_boundary = latest_synchronized_closed_boundary(
        store,
        normalized,
        timeframe,
        observed_at=generated,
    )
    if synchronized is None:
        missing = [
            symbol for symbol, boundary in per_asset_boundary.items()
            if boundary is None
        ]
        raise ValueError(
            "no fully closed stored candle is available for " + ",".join(missing)
        )
    reports: list[dict[str, object]] = []
    evidence_times: dict[str, str] = {}
    for symbol in normalized:
        candles = store.load_candles(symbol, timeframe, end=synchronized)
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
            as_of=synchronized,
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
        "as_of": synchronized.isoformat(),
        "observation_date": synchronized.date().isoformat(),
        "evidence_boundary": {
            "observed_at": generated.isoformat(),
            "synchronized_closed_open_time": synchronized.isoformat(),
            "per_asset_closed_open_time": {
                symbol: boundary.isoformat() if boundary is not None else None
                for symbol, boundary in sorted(per_asset_boundary.items())
            },
            "timeframe_duration_seconds": timeframe_duration(timeframe).total_seconds(),
            "fully_closed": True,
        },
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


def _promotion_evidence_eligible(payload: dict[str, Any]) -> bool:
    if payload.get("schema_version") != SNAPSHOT_SCHEMA_VERSION:
        return False
    boundary = payload.get("evidence_boundary", {})
    if boundary.get("fully_closed") is not True:
        return False
    try:
        as_of = _utc(datetime.fromisoformat(str(payload["as_of"])))
        observed = _utc(datetime.fromisoformat(str(boundary["observed_at"])))
        duration = timedelta(
            seconds=float(boundary["timeframe_duration_seconds"])
        )
        per_asset = boundary["per_asset_closed_open_time"]
        symbols = tuple(str(item) for item in payload["symbols"])
    except (KeyError, TypeError, ValueError):
        return False
    if duration <= timedelta(0) or as_of + duration > observed:
        return False
    if payload.get("observation_date") != as_of.date().isoformat():
        return False
    if boundary.get("synchronized_closed_open_time") != as_of.isoformat():
        return False
    if set(per_asset) != set(symbols):
        return False
    try:
        asset_boundaries = {
            symbol: _utc(datetime.fromisoformat(str(per_asset[symbol])))
            for symbol in symbols
        }
    except (TypeError, ValueError):
        return False
    if any(value < as_of or value + duration > observed for value in asset_boundaries.values()):
        return False
    return set(payload.get("evidence_as_of", {}).values()) == {as_of.isoformat()}


def _point(snapshot_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    validation = payload["validation"]
    aggregates = [market["aggregate"] for market in _markets(validation)]
    portfolio = payload["portfolio"]["summary"]
    mean_test_return = fmean(float(item["mean_test_return"]) for item in aggregates)
    mean_buy_hold_return = fmean(
        float(item.get("mean_buy_hold_return", 0.0)) for item in aggregates
    )
    return {
        "snapshot_id": snapshot_id,
        "as_of": payload["as_of"],
        "schema_version": payload.get("schema_version"),
        "promotion_evidence_eligible": _promotion_evidence_eligible(payload),
        "validation_strategy": payload["configuration"]["validation_strategy"],
        "portfolio_strategy": payload["configuration"]["portfolio_strategy"],
        "selected_candidates": _selected_candidates(validation),
        "warning_codes": _warning_codes(validation),
        "mean_validation_test_return": mean_test_return,
        "mean_validation_buy_hold_return": mean_buy_hold_return,
        "mean_validation_excess_return_vs_buy_hold": (
            mean_test_return - mean_buy_hold_return
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
    eligible_points = [
        point for point in points if point["promotion_evidence_eligible"]
    ]
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
        "promotion_eligible_points": eligible_points,
        "transitions": transitions,
        "summary": {
            "current_disposition": points[-1]["review_disposition"] if points else None,
            "consecutive_ready_snapshots": consecutive_ready,
            "parameter_change_events": parameter_change_events,
            "recurring_warning_counts": dict(sorted(warning_counts.items())),
            "history_warnings": history_warnings,
            "promotion_eligible_snapshot_count": len(eligible_points),
            "excluded_legacy_snapshot_count": len(points) - len(eligible_points),
        },
        "review_gate": {
            "disposition": (
                points[-1]["review_disposition"] if points else "DEFER"
            ),
            "live_execution_allowed": False,
        },
    }
