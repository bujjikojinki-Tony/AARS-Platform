from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from statistics import fmean
from typing import Any, Mapping, Sequence

from .coverage import analyze_funding_coverage
from .models import Candle, FundingCadenceObservation, FundingRate
from .proposal import candidate_from_parameters
from .simulation import ReplayEngine, ReplayResult, SimulationSummary
from .storage import MarketStore
from .validation import ValidationCandidate, strategy_for_candidate


EXECUTION_MODE = "PAPER_ONLY"
TRIAL_SCHEMA_VERSION = "mil3.paper-trial-result.v1"
WINDOWS: dict[str, timedelta | None] = {
    "30d": timedelta(days=30),
    "90d": timedelta(days=90),
    "180d": timedelta(days=180),
    "365d": timedelta(days=365),
    "all": None,
}


@dataclass(frozen=True)
class PaperTrialSettings:
    initial_equity_per_asset: float = 1000.0
    fee_rate: float = 0.0005
    slippage_rate: float = 0.0002
    maintenance_margin_rate: float = 0.005
    stop_max_drawdown: float = 0.20
    stop_max_liquidation_risk: float = 0.10

    def __post_init__(self) -> None:
        values = asdict(self)
        if any(not math.isfinite(float(value)) for value in values.values()):
            raise ValueError("paper trial settings must be finite")
        if self.initial_equity_per_asset <= 0:
            raise ValueError("initial equity must be positive")
        if self.fee_rate < 0 or self.slippage_rate < 0:
            raise ValueError("modeled costs must be non-negative")
        if self.maintenance_margin_rate < 0:
            raise ValueError("maintenance margin rate must be non-negative")
        if not 0 <= self.stop_max_drawdown <= 1:
            raise ValueError("drawdown stop must be between zero and one")
        if not 0 <= self.stop_max_liquidation_risk <= 1:
            raise ValueError("liquidation-risk stop must be between zero and one")


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _parse(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    return _utc(parsed)


def _candidate(payload: Mapping[str, Any], target: str, label: str) -> ValidationCandidate:
    validated = candidate_from_parameters(payload, target, label=label)
    validated.pop("candidate_id")
    return ValidationCandidate(**validated)


def _finite(value: float | int | str) -> float | int | str | None:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _summary(summary: SimulationSummary) -> dict[str, Any]:
    return {key: _finite(value) for key, value in summary.as_dict().items()}


def _mean_finite(values: Sequence[float | None]) -> float | None:
    finite = [float(value) for value in values if value is not None and math.isfinite(value)]
    return fmean(finite) if finite else None


def _aggregate(results: Sequence[ReplayResult]) -> dict[str, Any]:
    summaries = [item.summary for item in results]
    return {
        "asset_count": len(results),
        "initial_equity": sum(item.initial_equity for item in summaries),
        "final_equity": sum(item.final_equity for item in summaries),
        "mean_total_return": fmean(item.total_return for item in summaries),
        "worst_max_drawdown": max(item.max_drawdown for item in summaries),
        "mean_sharpe_approx": fmean(item.sharpe_approx for item in summaries),
        "mean_sortino": fmean(item.sortino for item in summaries),
        "mean_profit_factor": _mean_finite(
            [
                item.profit_factor if math.isfinite(item.profit_factor) else None
                for item in summaries
            ]
        ),
        "turnover_notional": sum(item.turnover_notional for item in summaries),
        "fees": sum(item.fees for item in summaries),
        "slippage": sum(item.slippage for item in summaries),
        "funding": sum(item.funding for item in summaries),
        "realized_pnl": sum(item.realized_pnl for item in summaries),
        "realized_grid_pnl": sum(item.realized_grid_pnl for item in summaries),
        "inventory_unrealized_pnl": sum(
            item.inventory_unrealized_pnl for item in summaries
        ),
        "mean_final_net_exposure": fmean(
            item.final_net_exposure for item in summaries
        ),
        "max_abs_net_exposure": max(item.max_abs_net_exposure for item in summaries),
        "mean_final_effective_leverage": fmean(
            item.final_effective_leverage for item in summaries
        ),
        "max_effective_leverage": max(
            item.max_effective_leverage for item in summaries
        ),
        "min_margin_buffer_pct": min(
            item.min_margin_buffer_pct for item in summaries
        ),
        "max_liquidation_risk": max(
            item.max_liquidation_risk for item in summaries
        ),
        "liquidation_events": sum(item.liquidation_events for item in summaries),
    }


def _delta(before: Mapping[str, Any], after: Mapping[str, Any]) -> dict[str, Any]:
    metrics = (
        "mean_total_return",
        "worst_max_drawdown",
        "mean_sharpe_approx",
        "mean_sortino",
        "mean_profit_factor",
        "turnover_notional",
        "fees",
        "slippage",
        "funding",
        "realized_pnl",
        "realized_grid_pnl",
        "inventory_unrealized_pnl",
        "mean_final_net_exposure",
        "max_abs_net_exposure",
        "mean_final_effective_leverage",
        "max_effective_leverage",
        "min_margin_buffer_pct",
        "max_liquidation_risk",
        "liquidation_events",
    )
    return {
        metric: (
            float(after[metric]) - float(before[metric])
            if before[metric] is not None and after[metric] is not None
            else None
        )
        for metric in metrics
    }


def _input_hash(
    candles: Sequence[Candle],
    funding: Sequence[FundingRate],
    cadence_observations: Sequence[FundingCadenceObservation],
) -> str:
    payload = {
        "candles": [
            [
                item.symbol,
                item.timeframe,
                item.open_time.isoformat(),
                item.open,
                item.high,
                item.low,
                item.close,
                item.volume,
            ]
            for item in candles
        ],
        "funding": [
            [
                item.symbol,
                item.funding_time.isoformat(),
                item.funding_rate,
                item.mark_price,
                item.rate_type,
            ]
            for item in funding
        ],
        "funding_cadence": [
            [
                item.symbol,
                item.observed_at.isoformat(),
                item.interval_hours,
                item.adjusted_rate_cap,
                item.adjusted_rate_floor,
                item.disclaimer,
                item.source_status,
            ]
            for item in cadence_observations
        ],
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _risk_score(summary: Mapping[str, Any]) -> float:
    sharpe = max(-5.0, min(5.0, float(summary["mean_sharpe_approx"])))
    sortino = max(-5.0, min(5.0, float(summary["mean_sortino"])))
    return (
        sharpe
        + 0.5 * sortino
        + float(summary["mean_total_return"])
        - 2.0 * float(summary["worst_max_drawdown"])
        - 2.0 * float(summary["max_liquidation_risk"])
        - 10.0 * int(summary["liquidation_events"])
    )


def build_paper_trial_result(
    store: MarketStore,
    proposal_envelope: Mapping[str, Any],
    *,
    settings: PaperTrialSettings = PaperTrialSettings(),
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    """Replay acknowledged baseline/proposed parameters without applying either."""
    if proposal_envelope.get("schema_version") != (
        "mil3.paper-configuration-proposal-envelope.v1"
    ):
        raise ValueError("unsupported paper proposal envelope schema")
    if proposal_envelope.get("execution_mode") != EXECUTION_MODE:
        raise ValueError("paper trial requires PAPER_ONLY proposal evidence")
    if proposal_envelope.get("status") != "ACKNOWLEDGED_FOR_PAPER_TRIAL":
        raise ValueError("paper trial requires acknowledged proposal review")
    for key in (
        "proposal_application_allowed",
        "automatic_strategy_change_allowed",
        "live_execution_allowed",
    ):
        if proposal_envelope.get(key) is not False:
            raise ValueError("paper proposal envelope exceeds trial authority")
    review = proposal_envelope.get("review") or {}
    if review.get("disposition") != "ACKNOWLEDGED_FOR_PAPER_TRIAL":
        raise ValueError("paper trial requires terminal acknowledgement evidence")
    if review.get("acknowledgement_applies_parameters") is not False:
        raise ValueError("paper trial acknowledgement must not apply parameters")
    if review.get("automatic_strategy_change_allowed") is not False:
        raise ValueError("paper trial acknowledgement must lock automatic changes")
    if review.get("live_execution_allowed") is not False:
        raise ValueError("paper trial acknowledgement must disallow live execution")

    proposal = proposal_envelope["proposal"]
    authority = proposal.get("authority", {})
    if any(
        authority.get(key) is not False
        for key in (
            "proposal_application_allowed",
            "automatic_strategy_change_allowed",
            "live_execution_allowed",
        )
    ):
        raise ValueError("paper proposal exceeds trial authority")
    proposal_id = str(proposal_envelope["proposal_id"])
    source_snapshot_id = str(proposal["source_evidence"]["shadow_snapshot_id"])
    snapshot = store.get_shadow_daily_snapshot(source_snapshot_id)
    if snapshot is None:
        raise ValueError("paper trial source snapshot is not archived")
    if snapshot.get("execution_mode") != EXECUTION_MODE:
        raise ValueError("paper trial source snapshot must be PAPER_ONLY")
    if snapshot.get("review_gate", {}).get("live_execution_allowed") is not False:
        raise ValueError("paper trial source snapshot must disallow live execution")

    configuration = snapshot.get("configuration", {})
    target = str(proposal["target_strategy"])
    if configuration.get("validation_strategy") != target:
        raise ValueError("paper trial strategy differs from source snapshot")
    timeframe = str(configuration.get("timeframe", ""))
    replay_window = str(configuration.get("replay_window", ""))
    warmup_bars = int(configuration.get("warmup_bars", 0))
    if not timeframe or replay_window not in WINDOWS or warmup_bars < 60:
        raise ValueError("paper trial source snapshot lacks replay configuration")
    symbols = tuple(str(item).upper() for item in snapshot.get("symbols", []))
    if not symbols or len(set(symbols)) != len(symbols):
        raise ValueError("paper trial source symbols are invalid")

    baseline_candidate = _candidate(
        proposal["baseline_parameters"], target, "trial baseline"
    )
    proposed_candidate = _candidate(
        proposal["proposed_parameters"], target, "trial proposed"
    )
    baseline_results: list[ReplayResult] = []
    proposed_results: list[ReplayResult] = []
    per_asset: list[dict[str, Any]] = []
    data_hashes: dict[str, str] = {}
    duration = WINDOWS[replay_window]

    for symbol in symbols:
        evidence_boundary = snapshot.get("evidence_as_of", {}).get(
            symbol, snapshot["as_of"]
        )
        end = _parse(str(evidence_boundary))
        start = end - duration if duration is not None else None
        candles = store.load_candles(
            symbol, timeframe, start=start, end=end
        )
        if len(candles) <= warmup_bars:
            raise ValueError(f"insufficient trial candles for {symbol}")
        if candles[-1].open_time != end:
            raise ValueError(f"trial evidence boundary missing for {symbol}")
        replay_start = candles[warmup_bars - 1].open_time
        funding = store.load_funding_rates(
            symbol, start=replay_start, end=candles[-1].open_time
        )
        proposed_strategy = strategy_for_candidate(proposed_candidate)
        baseline_strategy = strategy_for_candidate(baseline_candidate)
        funding_required = proposed_strategy.uses_funding or baseline_strategy.uses_funding
        cadence_observations = store.load_funding_cadence_observations(
            symbol,
            start=replay_start,
            end=candles[-1].open_time,
            include_previous=True,
        )
        coverage = analyze_funding_coverage(
            funding,
            replay_start,
            candles[-1].open_time,
            cadence_observations=cadence_observations,
            required=funding_required,
        )
        if funding_required and coverage.status != "COMPLETE":
            raise ValueError(
                f"complete funding history required for trial strategy {symbol}; "
                f"status={coverage.status}"
            )
        engine = ReplayEngine(
            initial_equity=settings.initial_equity_per_asset,
            fee_rate=settings.fee_rate,
            slippage_rate=settings.slippage_rate,
            funding_rates=funding,
            maintenance_margin_rate=settings.maintenance_margin_rate,
        )
        baseline_result = engine.run_detailed(
            candles, baseline_strategy, warmup_bars=warmup_bars
        )
        proposed_result = engine.run_detailed(
            candles, proposed_strategy, warmup_bars=warmup_bars
        )
        baseline_results.append(baseline_result)
        proposed_results.append(proposed_result)
        data_hashes[symbol] = _input_hash(
            candles, funding, cadence_observations
        )
        per_asset.append(
            {
                "symbol": symbol,
                "evidence_start": candles[0].open_time.isoformat(),
                "evidence_end": candles[-1].open_time.isoformat(),
                "bars": len(candles),
                "funding_events": len(funding),
                "funding_coverage": {
                    "status": coverage.status,
                    "coverage_ratio": coverage.coverage_ratio,
                    "estimated_missing_events": coverage.estimated_missing_events,
                    "cadence_hours": coverage.cadence_hours,
                    "cadence_source": coverage.cadence_source,
                },
                "input_sha256": data_hashes[symbol],
                "baseline": _summary(baseline_result.summary),
                "proposed": _summary(proposed_result.summary),
            }
        )

    baseline = _aggregate(baseline_results)
    proposed = _aggregate(proposed_results)
    deltas = _delta(baseline, proposed)
    stop_reasons: list[str] = []
    if proposed["worst_max_drawdown"] > settings.stop_max_drawdown:
        stop_reasons.append("MAX_DRAWDOWN_LIMIT_EXCEEDED")
    if proposed["max_liquidation_risk"] > settings.stop_max_liquidation_risk:
        stop_reasons.append("LIQUIDATION_RISK_LIMIT_EXCEEDED")
    if proposed["liquidation_events"]:
        stop_reasons.append("LIQUIDATION_APPROXIMATION_BREACH")
    if stop_reasons:
        disposition = "STOP_TRIAL"
    elif _risk_score(proposed) >= _risk_score(baseline):
        disposition = "ELIGIBLE_FOR_EXTENDED_PAPER_OBSERVATION"
    else:
        disposition = "CONTINUE_BASELINE"

    generated = _utc(generated_at or datetime.now(timezone.utc))
    combined_hash = hashlib.sha256(
        json.dumps(data_hashes, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "schema_version": TRIAL_SCHEMA_VERSION,
        "execution_mode": EXECUTION_MODE,
        "generated_at": generated.isoformat(),
        "proposal_id": proposal_id,
        "target_strategy": target,
        "source_snapshot_id": source_snapshot_id,
        "lifecycle": {
            "state": "COMPLETED",
            "events": [
                {"state": "ELIGIBILITY_CONFIRMED", "at": generated.isoformat()},
                {"state": "REPLAY_COMPLETED", "at": generated.isoformat()},
            ],
        },
        "configuration": {
            "symbols": list(symbols),
            "timeframe": timeframe,
            "replay_window": replay_window,
            "warmup_bars": warmup_bars,
            "baseline": baseline_candidate.as_dict(),
            "proposed": proposed_candidate.as_dict(),
            "settings": asdict(settings),
            "capital_model": "independent equal-capital asset buckets",
        },
        "input_evidence": {
            "combined_sha256": combined_hash,
            "per_asset_sha256": data_hashes,
            "reproducibility_scope": (
                "Content-addressed candles and funding consumed at the archived source "
                "boundaries; the source shadow snapshot did not embed raw market rows."
            ),
        },
        "results": {
            "aggregation": (
                "equal-weight mean returns/ratios; summed modeled costs and P&L; "
                "worst-asset drawdown, leverage, margin, and liquidation risk"
            ),
            "baseline": baseline,
            "proposed": proposed,
            "delta_proposed_minus_baseline": deltas,
            "per_asset": per_asset,
        },
        "stop_condition": {
            "triggered": bool(stop_reasons),
            "reasons": stop_reasons,
            "max_drawdown": settings.stop_max_drawdown,
            "max_liquidation_risk": settings.stop_max_liquidation_risk,
            "liquidation_events_allowed": 0,
        },
        "review_gate": {
            "disposition": disposition,
            "trial_application_allowed": False,
            "automatic_strategy_change_allowed": False,
            "live_execution_allowed": False,
        },
        "authority": {
            "trial_application_allowed": False,
            "automatic_strategy_change_allowed": False,
            "live_execution_allowed": False,
        },
    }
