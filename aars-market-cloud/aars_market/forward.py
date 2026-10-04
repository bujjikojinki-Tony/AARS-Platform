from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from .coverage import analyze_funding_coverage
from .proposal import candidate_from_parameters
from .simulation import ReplayEngine, ReplayResult
from .storage import MarketStore
from .trial import _aggregate, _delta, _input_hash, _risk_score
from .validation import ValidationCandidate, strategy_for_candidate


EXECUTION_MODE = "PAPER_ONLY"
FORWARD_SCHEMA_VERSION = "mil3.forward-observation.v1"


@dataclass(frozen=True)
class ForwardObservationSettings:
    minimum_forward_bars: int = 24
    confirmation_bars: int = 168

    def __post_init__(self) -> None:
        if self.minimum_forward_bars < 2:
            raise ValueError("minimum forward bars must be at least 2")
        if self.confirmation_bars < self.minimum_forward_bars:
            raise ValueError("confirmation bars must not precede minimum bars")


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _parse(value: str) -> datetime:
    return _utc(datetime.fromisoformat(value))


def _candidate(parameters: Mapping[str, Any], target: str, label: str) -> ValidationCandidate:
    payload = candidate_from_parameters(parameters, target, label=label)
    payload.pop("candidate_id")
    return ValidationCandidate(**payload)


def _summary(result: ReplayResult) -> dict[str, Any]:
    payload = result.summary.as_dict()
    return {
        key: None if isinstance(value, float) and not (-float("inf") < value < float("inf")) else value
        for key, value in payload.items()
    }


def build_forward_observation(
    store: MarketStore,
    trial_envelope: Mapping[str, Any],
    *,
    settings: ForwardObservationSettings = ForwardObservationSettings(),
    as_of: datetime | None = None,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    """Build one immutable checkpoint from market rows strictly after a trial boundary."""
    if trial_envelope.get("schema_version") != "mil3.paper-trial-result-envelope.v1":
        raise ValueError("unsupported paper trial envelope schema")
    if trial_envelope.get("execution_mode") != EXECUTION_MODE:
        raise ValueError("forward observation requires PAPER_ONLY trial evidence")
    for key in (
        "trial_application_allowed",
        "automatic_strategy_change_allowed",
        "live_execution_allowed",
    ):
        if trial_envelope.get(key) is not False:
            raise ValueError("paper trial envelope exceeds observation authority")

    trial = trial_envelope.get("trial") or {}
    trial_id = str(trial_envelope.get("trial_id", ""))
    if not trial_id or trial.get("schema_version") != "mil3.paper-trial-result.v1":
        raise ValueError("forward observation requires an archived paper trial")
    if trial.get("review_gate", {}).get("disposition") != "ELIGIBLE_FOR_EXTENDED_PAPER_OBSERVATION":
        raise ValueError("paper trial is not eligible for extended observation")
    if trial.get("stop_condition", {}).get("triggered") is not False:
        raise ValueError("stopped paper trial cannot enter forward observation")
    authority = trial.get("authority", {})
    if any(authority.get(key) is not False for key in (
        "trial_application_allowed",
        "automatic_strategy_change_allowed",
        "live_execution_allowed",
    )):
        raise ValueError("paper trial exceeds observation authority")

    configuration = trial.get("configuration", {})
    symbols = tuple(str(item).upper() for item in configuration.get("symbols", []))
    timeframe = str(configuration.get("timeframe", ""))
    warmup_bars = int(configuration.get("warmup_bars", 0))
    if not symbols or len(set(symbols)) != len(symbols) or not timeframe or warmup_bars < 60:
        raise ValueError("paper trial configuration is invalid")
    trial_assets = {
        str(item["symbol"]).upper(): item
        for item in trial.get("results", {}).get("per_asset", [])
    }
    if set(trial_assets) != set(symbols):
        raise ValueError("paper trial asset boundaries are incomplete")

    requested_end = _utc(as_of) if as_of is not None else None
    latest = []
    for symbol in symbols:
        value = store.latest_open_time(symbol, timeframe)
        if value is None:
            raise ValueError(f"no candles stored for {symbol} {timeframe}")
        latest.append(min(value, requested_end) if requested_end is not None else value)
    synchronized_end = min(latest)

    target = str(trial.get("target_strategy", ""))
    baseline_candidate = _candidate(configuration["baseline"], target, "forward baseline")
    proposed_candidate = _candidate(configuration["proposed"], target, "forward proposed")
    trial_settings = configuration.get("settings", {})
    engine_settings = {
        "initial_equity": float(trial_settings["initial_equity_per_asset"]),
        "fee_rate": float(trial_settings["fee_rate"]),
        "slippage_rate": float(trial_settings["slippage_rate"]),
        "maintenance_margin_rate": float(trial_settings["maintenance_margin_rate"]),
    }

    baseline_results: list[ReplayResult] = []
    proposed_results: list[ReplayResult] = []
    per_asset: list[dict[str, Any]] = []
    data_hashes: dict[str, str] = {}
    anchors: dict[str, str] = {}

    for symbol in symbols:
        anchor = _parse(str(trial_assets[symbol]["evidence_end"]))
        anchors[symbol] = anchor.isoformat()
        forward = [
            item for item in store.load_candles(symbol, timeframe, end=synchronized_end)
            if item.open_time > anchor
        ]
        if len(forward) < settings.minimum_forward_bars:
            raise ValueError(
                f"insufficient forward history for {symbol}; "
                f"required={settings.minimum_forward_bars} observed={len(forward)}"
            )
        context = store.load_candles(
            symbol, timeframe, limit=warmup_bars - 1, end=anchor
        )
        if len(context) != warmup_bars - 1 or context[-1].open_time != anchor:
            raise ValueError(f"forward warmup boundary missing for {symbol}")
        candles = [*context, *forward]
        replay_start = forward[0].open_time
        funding = store.load_funding_rates(symbol, start=replay_start, end=synchronized_end)
        cadence = store.load_funding_cadence_observations(
            symbol, start=replay_start, end=synchronized_end, include_previous=True
        )
        baseline_strategy = strategy_for_candidate(baseline_candidate)
        proposed_strategy = strategy_for_candidate(proposed_candidate)
        funding_required = baseline_strategy.uses_funding or proposed_strategy.uses_funding
        coverage = analyze_funding_coverage(
            funding,
            replay_start,
            synchronized_end,
            cadence_observations=cadence,
            required=funding_required,
        )
        if funding_required and coverage.status != "COMPLETE":
            raise ValueError(
                f"complete funding history required for forward observation {symbol}; "
                f"status={coverage.status}"
            )
        engine = ReplayEngine(funding_rates=funding, **engine_settings)
        baseline_result = engine.run_detailed(
            candles, baseline_strategy, warmup_bars=warmup_bars
        )
        proposed_result = engine.run_detailed(
            candles, proposed_strategy, warmup_bars=warmup_bars
        )
        if baseline_result.summary.bars != len(forward) or proposed_result.summary.bars != len(forward):
            raise ValueError("forward replay boundary accounting mismatch")
        baseline_results.append(baseline_result)
        proposed_results.append(proposed_result)
        data_hashes[symbol] = _input_hash(candles, funding, cadence)
        per_asset.append({
            "symbol": symbol,
            "trial_evidence_end": anchor.isoformat(),
            "forward_start": forward[0].open_time.isoformat(),
            "forward_end": forward[-1].open_time.isoformat(),
            "forward_bars": len(forward),
            "warmup_context_bars": len(context),
            "funding_events": len(funding),
            "funding_coverage": coverage.as_dict(),
            "input_sha256": data_hashes[symbol],
            "baseline": _summary(baseline_result),
            "proposed": _summary(proposed_result),
        })

    baseline = _aggregate(baseline_results)
    proposed = _aggregate(proposed_results)
    deltas = _delta(baseline, proposed)
    stop_reasons: list[str] = []
    if proposed["worst_max_drawdown"] > float(trial_settings["stop_max_drawdown"]):
        stop_reasons.append("MAX_DRAWDOWN_LIMIT_EXCEEDED")
    if proposed["max_liquidation_risk"] > float(trial_settings["stop_max_liquidation_risk"]):
        stop_reasons.append("LIQUIDATION_RISK_LIMIT_EXCEEDED")
    if proposed["liquidation_events"]:
        stop_reasons.append("LIQUIDATION_APPROXIMATION_BREACH")
    forward_bars = min(item["forward_bars"] for item in per_asset)
    if stop_reasons:
        disposition = "STOP_FORWARD_OBSERVATION"
    elif forward_bars < settings.confirmation_bars:
        disposition = "CONTINUE_FORWARD_OBSERVATION"
    elif _risk_score(proposed) >= _risk_score(baseline):
        disposition = "PROPOSED_EDGE_CONFIRMED"
    else:
        disposition = "PROPOSED_EDGE_NOT_CONFIRMED"

    previous = store.latest_forward_observation_for_trial(trial_id)
    if previous and _parse(previous["observed_through"]) == synchronized_end:
        archived = store.get_forward_observation(previous["observation_id"])
        lineage = archived["observation"]["lineage"] if archived else {}
    else:
        lineage = {
            "previous_observation_id": previous["observation_id"] if previous else None,
            "previous_input_sha256": previous["input_sha256"] if previous else None,
        }
    generated = _utc(generated_at or datetime.now(timezone.utc))
    combined_hash = hashlib.sha256(
        json.dumps(data_hashes, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "schema_version": FORWARD_SCHEMA_VERSION,
        "execution_mode": EXECUTION_MODE,
        "generated_at": generated.isoformat(),
        "trial_id": trial_id,
        "proposal_id": trial["proposal_id"],
        "target_strategy": target,
        "boundary": {
            "policy": "STRICTLY_AFTER_TRIAL_EVIDENCE_END",
            "trial_evidence_end_per_asset": anchors,
            "synchronized_forward_end": synchronized_end.isoformat(),
            "historical_replay_included": False,
            "warmup_context_affects_performance": False,
        },
        "configuration": {
            "symbols": list(symbols),
            "timeframe": timeframe,
            "warmup_bars": warmup_bars,
            "baseline": baseline_candidate.as_dict(),
            "proposed": proposed_candidate.as_dict(),
            "trial_settings": trial_settings,
            "observation_settings": asdict(settings),
        },
        "lineage": lineage,
        "input_evidence": {
            "combined_sha256": combined_hash,
            "per_asset_sha256": data_hashes,
            "scope": "All consumed warmup and forward candles plus forward funding and cadence are content-addressed; warmup is excluded from performance but retained for reproducibility.",
        },
        "results": {
            "forward_bars": forward_bars,
            "baseline": baseline,
            "proposed": proposed,
            "delta_proposed_minus_baseline": deltas,
            "per_asset": per_asset,
        },
        "stop_condition": {
            "triggered": bool(stop_reasons),
            "reasons": stop_reasons,
            "max_drawdown": float(trial_settings["stop_max_drawdown"]),
            "max_liquidation_risk": float(trial_settings["stop_max_liquidation_risk"]),
            "liquidation_events_allowed": 0,
        },
        "review_gate": {
            "disposition": disposition,
            "confirmation_bars_required": settings.confirmation_bars,
            "observation_application_allowed": False,
            "automatic_strategy_change_allowed": False,
            "live_execution_allowed": False,
        },
        "authority": {
            "observation_application_allowed": False,
            "automatic_strategy_change_allowed": False,
            "live_execution_allowed": False,
        },
    }
