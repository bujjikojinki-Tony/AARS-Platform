from __future__ import annotations

import json
import math
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from .features import compute_features
from .models import Candle
from .policy import decide_target_exposure
from .probability import estimate_outcome_probabilities
from .simulation import EXECUTION_MODE, ReplayResult, compare_shadow_strategy_results
from .state_engine import classify_market_state


DASHBOARD_SCHEMA_VERSION = "mil3.dashboard.v1"


def _utc_iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def _finite(value: float) -> float | None:
    return value if math.isfinite(value) else None


def _downsample_trace(result: ReplayResult, max_points: int) -> list[dict[str, Any]]:
    trace = result.trace
    if max_points <= 0:
        raise ValueError("max_trace_points must be positive")
    step = max(1, math.ceil(len(trace) / max_points))
    selected = list(trace[::step])
    if trace and selected[-1] != trace[-1]:
        selected.append(trace[-1])
    return [
        {
            **asdict(point),
            "effective_leverage": _finite(point.effective_leverage),
        }
        for point in selected
    ]


def _strategy_payload(result: ReplayResult, max_trace_points: int) -> dict[str, Any]:
    summary = result.summary.as_dict()
    profit_factor = float(summary["profit_factor"])
    summary["profit_factor"] = _finite(profit_factor)
    summary["profit_factor_label"] = "INF" if not math.isfinite(profit_factor) else f"{profit_factor:.2f}"
    return {
        "id": result.summary.strategy,
        "summary": summary,
        "trace": _downsample_trace(result, max_trace_points),
    }


def _risk_level(risk: float, liquidation_events: int) -> str:
    if liquidation_events:
        return "CRITICAL"
    if risk >= 0.25:
        return "HIGH"
    if risk >= 0.10:
        return "ELEVATED"
    return "NORMAL"


def build_dashboard_payload(
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
    data_fresh: bool | None = None,
    source: str = "SQLite normalized candles",
    generated_at: datetime | None = None,
    max_trace_points: int = 240,
    replay_results: Sequence[ReplayResult] | None = None,
) -> dict[str, Any]:
    if len(candles) <= warmup_bars:
        raise ValueError("insufficient candles for dashboard payload")

    results = list(replay_results) if replay_results is not None else compare_shadow_strategy_results(
        candles,
        initial_equity=initial_equity,
        warmup_bars=warmup_bars,
        futures_leverage=futures_leverage,
        aars_max_abs_exposure=aars_max_abs_exposure,
        grid_spacing_pct=grid_spacing_pct,
        grid_levels=grid_levels,
        tactical_hedge=tactical_hedge,
        fee_rate=fee_rate,
        slippage_rate=slippage_rate,
        funding_rate_per_bar=funding_rate_per_bar,
        maintenance_margin_rate=maintenance_margin_rate,
    )
    if not results:
        raise ValueError("replay_results must not be empty")

    latest_features = compute_features(candles)
    assessment = classify_market_state(latest_features)
    probabilities = estimate_outcome_probabilities(assessment, horizon_bars=24)
    decision = decide_target_exposure(
        assessment,
        probabilities,
        max_abs_exposure=aars_max_abs_exposure,
    )

    highest = max(results, key=lambda item: item.summary.max_liquidation_risk)
    highest_risk = highest.summary.max_liquidation_risk
    liquidation_events = sum(item.summary.liquidation_events for item in results)
    risk_level = _risk_level(highest_risk, liquidation_events)
    freshness_status = "CURRENT" if data_fresh is True else "STALE" if data_fresh is False else "UNKNOWN"
    degraded = data_fresh is not True

    alerts: list[dict[str, Any]] = []
    if degraded:
        alerts.append(
            {
                "id": "DATA_FRESHNESS",
                "severity": "HIGH" if data_fresh is False else "ELEVATED",
                "object": candles[-1].symbol,
                "trigger": f"market data status is {freshness_status}",
                "impact": "Current-state interpretation may not represent the live market.",
                "recommended_action": "Refresh public candles, regenerate the payload, then review Latest Stable View.",
                "status": "OPEN",
                "closure_condition": "Freshness gate returns CURRENT.",
            }
        )
    if liquidation_events:
        alerts.append(
            {
                "id": "LIQUIDATION_BREACH",
                "severity": "CRITICAL",
                "object": highest.summary.strategy,
                "trigger": f"{liquidation_events} replay bars breached the maintenance-margin approximation",
                "impact": "The leveraged shadow strategy would be non-viable under the configured approximation.",
                "recommended_action": "Reduce leverage or grid inventory before accepting the strategy for shadow monitoring.",
                "status": "OPEN",
                "closure_condition": "Zero approximation breaches on the acceptance replay window.",
            }
        )
    elif futures_leverage >= 5:
        alerts.append(
            {
                "id": "LEVERAGE_WATCH",
                "severity": "ELEVATED",
                "object": highest.summary.strategy,
                "trigger": f"configured futures leverage is {futures_leverage:g}x",
                "impact": "Small price changes can materially compress margin buffer.",
                "recommended_action": "Treat this as a stress test and review the leverage and liquidation traces.",
                "status": "MONITORING",
                "closure_condition": "Leverage is reduced below 5x or an explicit risk exception is recorded.",
            }
        )

    generated = generated_at or datetime.now(timezone.utc)
    return {
        "schema_version": DASHBOARD_SCHEMA_VERSION,
        "generated_at": _utc_iso(generated),
        "execution_mode": EXECUTION_MODE,
        "market": {
            "symbol": candles[-1].symbol,
            "timeframe": candles[-1].timeframe,
            "bars": len(candles),
            "source": source,
            "latest_candle_at": _utc_iso(candles[-1].open_time),
            "freshness_status": freshness_status,
            "degraded": degraded,
            "degraded_reason": None if not degraded else "Fresh replay data is not confirmed.",
        },
        "highest_risk": {
            "level": risk_level,
            "strategy": highest.summary.strategy,
            "liquidation_risk": highest_risk,
            "liquidation_events": liquidation_events,
            "min_margin_buffer_pct": highest.summary.min_margin_buffer_pct,
        },
        "latest_stable_view": {
            "as_of": _utc_iso(candles[-1].open_time),
            "state": assessment.state.value,
            "confidence": assessment.confidence,
            "probabilities": asdict(probabilities),
            "recommended_exposure": decision.target_exposure,
            "decision_reason": decision.reason,
            "evidence": list(assessment.evidence),
            "counter_evidence": list(assessment.counter_evidence),
            "status": "DEGRADED" if degraded else "STABLE",
        },
        "parameters": {
            "initial_equity": initial_equity,
            "warmup_bars": warmup_bars,
            "futures_leverage": futures_leverage,
            "aars_max_abs_exposure": aars_max_abs_exposure,
            "grid_spacing_pct": grid_spacing_pct,
            "grid_levels": grid_levels,
            "tactical_hedge": tactical_hedge,
            "fee_rate": fee_rate,
            "slippage_rate": slippage_rate,
            "funding_rate_per_bar": funding_rate_per_bar,
            "maintenance_margin_rate": maintenance_margin_rate,
            "intrabar_path_model": "green: prev-close/open/low/high/close; red: prev-close/open/high/low/close",
        },
        "strategies": [_strategy_payload(result, max_trace_points) for result in results],
        "alerts": alerts,
        "review_gate": {
            "disposition": "DEFER" if degraded or liquidation_events else "ACCEPT_WITH_MONITORING",
            "reasons": [alert["id"] for alert in alerts],
            "live_execution_allowed": False,
        },
    }


def write_dashboard_payload(path: str | Path, payload: dict[str, Any]) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    return target
