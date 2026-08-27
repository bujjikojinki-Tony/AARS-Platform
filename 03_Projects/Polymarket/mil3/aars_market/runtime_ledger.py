from __future__ import annotations

import hashlib
import math
from datetime import datetime, timedelta, timezone
from statistics import fmean
from typing import Any, Mapping, Sequence

from .coverage import analyze_funding_coverage
from .isolated_config import canonical_sha256
from .models import Candle, FundingCadenceObservation, FundingRate
from .simulation import ReplayEngine, SimulationSummary
from .storage import MarketStore
from .validation import ValidationCandidate, strategy_for_candidate


EXECUTION_MODE = "PAPER_ONLY"
SNAPSHOT_SCHEMA_VERSION = "mil3.isolated-paper-market-snapshot.v1"
LEDGER_SCHEMA_VERSION = "mil3.isolated-paper-ledger-result.v1"
WINDOWS: dict[str, timedelta | None] = {
    "30d": timedelta(days=30),
    "90d": timedelta(days=90),
    "180d": timedelta(days=180),
    "365d": timedelta(days=365),
    "all": None,
}


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _parse(value: str) -> datetime:
    return _utc(datetime.fromisoformat(value))


def _candidate(configuration: Mapping[str, Any]) -> ValidationCandidate:
    payload = dict(configuration.get("proposed", {}))
    payload.pop("candidate_id", None)
    return ValidationCandidate(**payload)


def _input_payload(
    candles: Sequence[Candle],
    funding: Sequence[FundingRate],
    cadence: Sequence[FundingCadenceObservation],
) -> dict[str, Any]:
    return {
        "candles": [
            [
                item.symbol, item.timeframe, item.open_time.isoformat(), item.open,
                item.high, item.low, item.close, item.volume,
            ]
            for item in candles
        ],
        "funding": [
            [
                item.symbol, item.funding_time.isoformat(), item.funding_rate,
                item.mark_price, item.rate_type,
            ]
            for item in funding
        ],
        "funding_cadence": [
            [
                item.symbol, item.observed_at.isoformat(), item.interval_hours,
                item.adjusted_rate_cap, item.adjusted_rate_floor, item.disclaimer,
                item.source_status,
            ]
            for item in cadence
        ],
    }


def _configuration_contract(configuration: Mapping[str, Any]) -> tuple[
    tuple[str, ...], str, str, int, ValidationCandidate, Mapping[str, Any]
]:
    symbols = tuple(str(item).upper() for item in configuration.get("symbols", []))
    timeframe = str(configuration.get("timeframe", ""))
    replay_window = str(configuration.get("replay_window", ""))
    warmup_bars = int(configuration.get("warmup_bars", 0))
    settings = configuration.get("settings", {})
    if not symbols or len(set(symbols)) != len(symbols):
        raise ValueError("runtime configuration symbols are invalid")
    if not timeframe or replay_window not in WINDOWS or warmup_bars < 60:
        raise ValueError("runtime configuration replay boundary is invalid")
    required_settings = {
        "initial_equity_per_asset", "fee_rate", "slippage_rate",
        "maintenance_margin_rate",
    }
    if not required_settings.issubset(settings):
        raise ValueError("runtime configuration paper-ledger settings are incomplete")
    candidate = _candidate(configuration)
    return symbols, timeframe, replay_window, warmup_bars, candidate, settings


def build_runtime_market_snapshot(
    store: MarketStore,
    session_id: str,
    *,
    observed_at: datetime | None = None,
    boundary: datetime | None = None,
) -> dict[str, Any]:
    """Build a content-addressed snapshot from stored public market data only."""
    evaluated = _utc(observed_at or datetime.now(timezone.utc))
    session = store.resolve_isolated_paper_runtime_session(session_id, now=evaluated)
    if session["effective_status"] != "RUNNING":
        raise ValueError(
            f"paper cycle requires an effective runtime lease: {session['effective_status']}"
        )
    registry = store.get_isolated_paper_configuration(session["configuration_id"])
    if registry is None or registry.get("configuration_sha256") != session["configuration_sha256"]:
        raise ValueError("runtime configuration payload/hash is unavailable")
    configuration = registry["configuration"]
    symbols, timeframe, replay_window, warmup_bars, candidate, _ = (
        _configuration_contract(configuration)
    )
    if boundary is None:
        latest = []
        for symbol in symbols:
            rows = store.load_candles(symbol, timeframe, limit=1, end=evaluated)
            if not rows:
                raise ValueError(f"no stored candle is available for {symbol} at cycle time")
            latest.append(rows[-1].open_time)
        synchronized = min(latest)
    else:
        synchronized = _utc(boundary)
        if synchronized > evaluated:
            raise ValueError("runtime snapshot boundary cannot exceed cycle time")
    duration = WINDOWS[replay_window]
    start = synchronized - duration if duration is not None else None
    assets: list[dict[str, Any]] = []
    asset_hashes: dict[str, str] = {}
    for symbol in symbols:
        candles = store.load_candles(
            symbol, timeframe, start=start, end=synchronized
        )
        if len(candles) <= warmup_bars or candles[-1].open_time != synchronized:
            raise ValueError(f"insufficient synchronized runtime candles for {symbol}")
        replay_start = candles[warmup_bars - 1].open_time
        funding = store.load_funding_rates(symbol, start=replay_start, end=synchronized)
        cadence = store.load_funding_cadence_observations(
            symbol, start=replay_start, end=synchronized, include_previous=True
        )
        coverage = analyze_funding_coverage(
            funding,
            replay_start,
            synchronized,
            cadence_observations=cadence,
            required=strategy_for_candidate(candidate).uses_funding,
        )
        if strategy_for_candidate(candidate).uses_funding and coverage.status != "COMPLETE":
            raise ValueError(
                f"complete funding history required for runtime {symbol}; status={coverage.status}"
            )
        input_sha = canonical_sha256(_input_payload(candles, funding, cadence))
        asset_hashes[symbol] = input_sha
        assets.append({
            "symbol": symbol,
            "timeframe": timeframe,
            "evidence_start": candles[0].open_time.isoformat(),
            "replay_start": replay_start.isoformat(),
            "evidence_end": synchronized.isoformat(),
            "bars": len(candles),
            "funding_events": len(funding),
            "cadence_observations": len(cadence),
            "input_sha256": input_sha,
            "funding_coverage": {
                "status": coverage.status,
                "coverage_ratio": coverage.coverage_ratio,
                "estimated_missing_events": coverage.estimated_missing_events,
                "cadence_hours": coverage.cadence_hours,
                "cadence_source": coverage.cadence_source,
            },
        })
    cycle_identity = {
        "sandbox_id": session["sandbox_id"],
        "configuration_id": session["configuration_id"],
        "snapshot_boundary": synchronized.isoformat(),
    }
    payload = {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "execution_mode": EXECUTION_MODE,
        "cycle_id": canonical_sha256(cycle_identity)[:24],
        "sandbox_id": session["sandbox_id"],
        "configuration_id": session["configuration_id"],
        "configuration_sha256": session["configuration_sha256"],
        "snapshot_boundary": synchronized.isoformat(),
        "symbols": list(symbols),
        "timeframe": timeframe,
        "replay_window": replay_window,
        "warmup_bars": warmup_bars,
        "assets": assets,
        "combined_input_sha256": canonical_sha256(asset_hashes),
        "source": "LOCAL_NORMALIZED_PUBLIC_MARKET_STORE",
        "authority": {
            "source_rows_read_only": True,
            "paper_calculation_only": True,
            "order_path_present": False,
            "live_execution_allowed": False,
        },
    }
    payload["snapshot_sha256"] = canonical_sha256(payload)
    return payload


def verify_runtime_market_snapshot(snapshot: Mapping[str, Any]) -> bool:
    if snapshot.get("schema_version") != SNAPSHOT_SCHEMA_VERSION:
        return False
    if snapshot.get("execution_mode") != EXECUTION_MODE:
        return False
    authority = snapshot.get("authority", {})
    if authority != {
        "source_rows_read_only": True,
        "paper_calculation_only": True,
        "order_path_present": False,
        "live_execution_allowed": False,
    }:
        return False
    identity = {
        "sandbox_id": snapshot.get("sandbox_id"),
        "configuration_id": snapshot.get("configuration_id"),
        "snapshot_boundary": snapshot.get("snapshot_boundary"),
    }
    if snapshot.get("cycle_id") != canonical_sha256(identity)[:24]:
        return False
    unhashed = dict(snapshot)
    supplied = unhashed.pop("snapshot_sha256", None)
    return supplied == canonical_sha256(unhashed)


def _finite_summary(summary: SimulationSummary) -> dict[str, Any]:
    return {
        key: None if isinstance(value, float) and not math.isfinite(value) else value
        for key, value in summary.as_dict().items()
    }


def _finite_number(value: float | int) -> float | int | None:
    return value if not isinstance(value, float) or math.isfinite(value) else None


def _finite_metric(ledgers: Sequence[Mapping[str, Any]], key: str) -> list[float]:
    return [
        float(item[key])
        for item in ledgers
        if item.get(key) is not None and math.isfinite(float(item[key]))
    ]


def calculate_runtime_paper_ledger(
    store: MarketStore,
    snapshot: Mapping[str, Any],
    *,
    calculated_at: datetime | None = None,
) -> dict[str, Any]:
    """Recompute the configured paper ledger through the immutable boundary."""
    if not verify_runtime_market_snapshot(snapshot):
        raise ValueError("runtime market snapshot integrity failed")
    registry = store.get_isolated_paper_configuration(str(snapshot["configuration_id"]))
    if registry is None or registry.get("configuration_sha256") != snapshot.get(
        "configuration_sha256"
    ):
        raise ValueError("runtime ledger configuration identity changed")
    configuration = registry["configuration"]
    symbols, timeframe, _, warmup_bars, candidate, settings = _configuration_contract(
        configuration
    )
    if tuple(snapshot["symbols"]) != symbols or snapshot["timeframe"] != timeframe:
        raise ValueError("runtime snapshot differs from configuration scope")
    boundary = _parse(str(snapshot["snapshot_boundary"]))
    per_asset: list[dict[str, Any]] = []
    for asset in snapshot["assets"]:
        symbol = str(asset["symbol"])
        candles = store.load_candles(
            symbol,
            timeframe,
            start=_parse(str(asset["evidence_start"])),
            end=boundary,
        )
        funding = store.load_funding_rates(
            symbol, start=_parse(str(asset["replay_start"])), end=boundary
        )
        cadence = store.load_funding_cadence_observations(
            symbol,
            start=_parse(str(asset["replay_start"])),
            end=boundary,
            include_previous=True,
        )
        if canonical_sha256(_input_payload(candles, funding, cadence)) != asset[
            "input_sha256"
        ]:
            raise ValueError(f"runtime snapshot source drift detected for {symbol}")
        result = ReplayEngine(
            initial_equity=float(settings["initial_equity_per_asset"]),
            fee_rate=float(settings["fee_rate"]),
            slippage_rate=float(settings["slippage_rate"]),
            funding_rates=funding,
            maintenance_margin_rate=float(settings["maintenance_margin_rate"]),
        ).run_detailed(
            candles, strategy_for_candidate(candidate), warmup_bars=warmup_bars
        )
        per_asset.append({
            "symbol": symbol,
            "input_sha256": asset["input_sha256"],
            "ledger": _finite_summary(result.summary),
            "last_trace": {
                "as_of": result.trace[-1].as_of,
                "mark_price": result.trace[-1].mark_price,
                "equity": result.trace[-1].equity,
                "drawdown": result.trace[-1].drawdown,
                "net_exposure": result.trace[-1].net_exposure,
                "effective_leverage": _finite_number(
                    result.trace[-1].effective_leverage
                ),
                "margin_buffer_pct": _finite_number(
                    result.trace[-1].margin_buffer_pct
                ),
                "liquidation_risk": _finite_number(
                    result.trace[-1].liquidation_risk
                ),
            },
        })
    ledgers = [item["ledger"] for item in per_asset]
    returns = _finite_metric(ledgers, "total_return")
    drawdowns = _finite_metric(ledgers, "max_drawdown")
    leverages = _finite_metric(ledgers, "max_effective_leverage")
    margin_buffers = _finite_metric(ledgers, "min_margin_buffer_pct")
    liquidation_risks = _finite_metric(ledgers, "max_liquidation_risk")
    aggregate = {
        "asset_count": len(ledgers),
        "initial_equity": sum(float(item["initial_equity"]) for item in ledgers),
        "final_equity": sum(float(item["final_equity"]) for item in ledgers),
        "mean_total_return": fmean(returns) if returns else None,
        "worst_max_drawdown": max(drawdowns) if drawdowns else None,
        "turnover_notional": sum(float(item["turnover_notional"]) for item in ledgers),
        "fees": sum(float(item["fees"]) for item in ledgers),
        "slippage": sum(float(item["slippage"]) for item in ledgers),
        "funding": sum(float(item["funding"]) for item in ledgers),
        "realized_pnl": sum(float(item["realized_pnl"]) for item in ledgers),
        "realized_grid_pnl": sum(float(item["realized_grid_pnl"]) for item in ledgers),
        "inventory_unrealized_pnl": sum(
            float(item["inventory_unrealized_pnl"]) for item in ledgers
        ),
        "max_effective_leverage": max(leverages) if leverages else None,
        "min_margin_buffer_pct": min(margin_buffers) if margin_buffers else None,
        "max_liquidation_risk": max(liquidation_risks) if liquidation_risks else None,
        "liquidation_events": sum(int(item["liquidation_events"]) for item in ledgers),
    }
    calculated = _utc(calculated_at or datetime.now(timezone.utc))
    deterministic = {
        "cycle_id": snapshot["cycle_id"],
        "snapshot_sha256": snapshot["snapshot_sha256"],
        "configuration_sha256": snapshot["configuration_sha256"],
        "strategy": candidate.as_dict(),
        "aggregate": aggregate,
        "per_asset": per_asset,
    }
    payload = {
        "schema_version": LEDGER_SCHEMA_VERSION,
        "execution_mode": EXECUTION_MODE,
        "result_id": canonical_sha256(deterministic)[:24],
        "calculated_at": calculated.isoformat(),
        **deterministic,
        "authority": {
            "deterministic_paper_calculation": True,
            "market_source_read_only": True,
            "paper_orders_created": False,
            "order_path_present": False,
            "live_execution_allowed": False,
        },
    }
    unhashed = dict(payload)
    payload["result_sha256"] = canonical_sha256(unhashed)
    return payload


def verify_runtime_paper_ledger(result: Mapping[str, Any]) -> bool:
    if result.get("schema_version") != LEDGER_SCHEMA_VERSION:
        return False
    if result.get("execution_mode") != EXECUTION_MODE:
        return False
    if result.get("authority") != {
        "deterministic_paper_calculation": True,
        "market_source_read_only": True,
        "paper_orders_created": False,
        "order_path_present": False,
        "live_execution_allowed": False,
    }:
        return False
    deterministic = {
        "cycle_id": result.get("cycle_id"),
        "snapshot_sha256": result.get("snapshot_sha256"),
        "configuration_sha256": result.get("configuration_sha256"),
        "strategy": result.get("strategy"),
        "aggregate": result.get("aggregate"),
        "per_asset": result.get("per_asset"),
    }
    if result.get("result_id") != canonical_sha256(deterministic)[:24]:
        return False
    unhashed = dict(result)
    supplied = unhashed.pop("result_sha256", None)
    return supplied == canonical_sha256(unhashed)


def execute_runtime_paper_cycle(
    store: MarketStore,
    session_id: str,
    fencing_token: str,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Reserve, calculate and atomically commit one idempotent paper cycle."""
    calculated = _utc(now or datetime.now(timezone.utc))
    snapshot = build_runtime_market_snapshot(store, session_id, observed_at=calculated)
    token_hash = hashlib.sha256(fencing_token.encode("utf-8")).hexdigest()
    reservation = store.reserve_isolated_paper_runtime_cycle(
        session_id,
        fencing_token_sha256=token_hash,
        snapshot=snapshot,
        now=calculated,
    )
    if reservation["status"] == "REUSED_COMMITTED":
        result = store.get_isolated_paper_ledger_result(reservation["result_id"])
        if result is None or not verify_runtime_paper_ledger(result):
            raise ValueError("committed runtime paper ledger is unavailable or invalid")
        return {
            "status": "REUSED_COMMITTED",
            "cycle_id": reservation["cycle_id"],
            "result_id": reservation["result_id"],
            "checkpoint_version": reservation["checkpoint_version"],
            "snapshot_boundary": snapshot["snapshot_boundary"],
            "snapshot_sha256": snapshot["snapshot_sha256"],
            "result": result,
            "duplicate_application_prevented": True,
        }
    result = calculate_runtime_paper_ledger(
        store, snapshot, calculated_at=calculated
    )
    committed = store.commit_isolated_paper_runtime_cycle(
        session_id,
        fencing_token_sha256=token_hash,
        result=result,
        now=calculated,
    )
    return {
        **committed,
        "reservation_status": reservation["status"],
        "snapshot_boundary": snapshot["snapshot_boundary"],
        "snapshot_sha256": snapshot["snapshot_sha256"],
        "result": result,
        "duplicate_application_prevented": False,
    }
