from __future__ import annotations

import math
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Mapping, Sequence

from .isolated_config import canonical_sha256
from .isolated_runtime import IsolatedRuntimeSettings, run_isolated_paper_runtime
from .runtime_ledger import (
    latest_synchronized_closed_boundary,
    timeframe_duration,
    verify_runtime_paper_ledger,
)
from .storage import MarketStore


EXECUTION_MODE = "PAPER_ONLY"
FORWARD_OPS_SCHEMA_VERSION = "mil3.forward-bot-operations.v1"
FORWARD_WAKE_SCHEMA_VERSION = "mil3.forward-bot-wake.v1"
DELTA_METRICS = (
    "final_equity",
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
    "max_effective_leverage",
    "min_margin_buffer_pct",
    "max_liquidation_risk",
    "liquidation_events",
)
ACCOUNT_DELTA_METRICS = (
    "equity",
    "position_qty",
    "realized_pnl",
    "unrealized_pnl",
    "fees",
    "funding",
    "net_exposure",
    "effective_leverage",
    "margin_buffer_pct",
    "liquidation_risk",
)


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _parse(value: str) -> datetime:
    return _utc(datetime.fromisoformat(value))


def _delta(before: object, after: object) -> float | int | None:
    if before is None or after is None:
        return None
    try:
        result = float(after) - float(before)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(result):
        return None
    if isinstance(before, int) and isinstance(after, int):
        return int(result)
    return result


def _alert(
    code: str,
    severity: str,
    object_id: str,
    trigger: str,
    impact: str,
    response: str,
) -> dict[str, str]:
    return {
        "code": code,
        "severity": severity,
        "object": object_id,
        "trigger": trigger,
        "impact": impact,
        "recommended_response": response,
    }


def _bot_map(result: Mapping[str, Any] | None) -> dict[str, Mapping[str, Any]]:
    if result is None or not verify_runtime_paper_ledger(result):
        return {}
    fleet = result.get("bot_fleet")
    if not isinstance(fleet, Mapping):
        return {}
    return {
        str(item["bot_id"]): item
        for item in fleet.get("bots", [])
        if isinstance(item, Mapping) and item.get("bot_id")
    }


def build_cycle_account_deltas(
    current: Mapping[str, Any] | None,
    previous: Mapping[str, Any] | None,
) -> dict[str, Any]:
    current_bots = _bot_map(current)
    previous_bots = _bot_map(previous)
    if not current_bots:
        return {
            "status": "UNAVAILABLE",
            "previous_result_id": previous.get("result_id") if previous else None,
            "current_result_id": current.get("result_id") if current else None,
            "bots": [],
        }
    if previous is not None and not previous_bots:
        return {
            "status": "UNAVAILABLE",
            "previous_result_id": previous.get("result_id"),
            "current_result_id": current.get("result_id") if current else None,
            "bots": [],
        }
    bot_deltas = []
    for bot_id, bot in current_bots.items():
        before_bot = previous_bots.get(bot_id)
        aggregate = bot["aggregate"]
        before_aggregate = before_bot["aggregate"] if before_bot else {}
        before_assets = {
            str(item["symbol"]): item for item in before_bot.get("per_asset", [])
        } if before_bot else {}
        asset_deltas = []
        for asset in bot.get("per_asset", []):
            symbol = str(asset["symbol"])
            account = asset["account"]
            before_account = before_assets.get(symbol, {}).get("account", {})
            current_fills = int(
                account.get("fill_evidence", {}).get("simulated_fill_count", 0)
            )
            previous_fills = int(
                before_account.get("fill_evidence", {}).get("simulated_fill_count", 0)
            )
            asset_deltas.append({
                "symbol": symbol,
                "metrics": {
                    key: _delta(before_account.get(key), account.get(key))
                    for key in ACCOUNT_DELTA_METRICS
                },
                "new_simulated_fills": (
                    current_fills - previous_fills if before_bot else current_fills
                ),
                "current_risk_state": asset["risk"]["state"],
            })
        bot_deltas.append({
            "bot_id": bot_id,
            "account_id": bot["account_id"],
            "lineage": "DELTA" if before_bot else "GENESIS",
            "metrics": {
                key: _delta(before_aggregate.get(key), aggregate.get(key))
                for key in DELTA_METRICS
            },
            "per_asset": asset_deltas,
        })
    return {
        "status": "DELTA" if previous_bots else "GENESIS",
        "previous_result_id": previous.get("result_id") if previous else None,
        "current_result_id": current.get("result_id") if current else None,
        "bots": bot_deltas,
    }


def calculate_continuous_burn_in(
    boundaries: Sequence[datetime],
    *,
    interval: timedelta,
    minimum_days: int,
    target_days: int,
) -> dict[str, Any]:
    ordered = sorted(set(boundaries))
    if not ordered:
        return {
            "status": "NOT_STARTED",
            "continuous_start": None,
            "latest_boundary": None,
            "continuous_cycles": 0,
            "observed_days": 0.0,
            "minimum_days": minimum_days,
            "target_days": target_days,
            "minimum_progress": 0.0,
            "target_progress": 0.0,
            "minimum_ready": False,
            "target_ready": False,
            "max_gap_seconds": None,
        }
    continuous_start = ordered[-1]
    suffix_count = 1
    max_gap = timedelta(0)
    for before, after in reversed(list(zip(ordered[:-1], ordered[1:]))):
        gap = after - before
        max_gap = max(max_gap, gap)
        if gap > interval * 2:
            break
        continuous_start = before
        suffix_count += 1
    observed = ordered[-1] + interval - continuous_start
    observed_days = max(0.0, observed.total_seconds() / 86400.0)
    minimum_ready = observed_days >= minimum_days
    target_ready = observed_days >= target_days
    status = (
        "TARGET_14D_REACHED" if target_ready else
        "MINIMUM_7D_REACHED" if minimum_ready else
        "BURN_IN_RUNNING"
    )
    return {
        "status": status,
        "continuous_start": continuous_start.isoformat(),
        "latest_boundary": ordered[-1].isoformat(),
        "continuous_cycles": suffix_count,
        "observed_days": observed_days,
        "minimum_days": minimum_days,
        "target_days": target_days,
        "minimum_progress": min(1.0, observed_days / minimum_days),
        "target_progress": min(1.0, observed_days / target_days),
        "minimum_ready": minimum_ready,
        "target_ready": target_ready,
        "max_gap_seconds": max_gap.total_seconds(),
    }


def build_forward_bot_operations_view(
    store: MarketStore,
    sandbox_id: str,
    *,
    now: datetime | None = None,
    stale_closed_bars: int = 2,
    reserved_timeout: timedelta = timedelta(minutes=5),
    minimum_burn_in_days: int = 7,
    target_burn_in_days: int = 14,
) -> dict[str, Any]:
    if stale_closed_bars <= 0 or reserved_timeout <= timedelta(0):
        raise ValueError("forward operation age limits must be positive")
    if minimum_burn_in_days <= 0 or target_burn_in_days < minimum_burn_in_days:
        raise ValueError("burn-in targets are invalid")
    evaluated = _utc(now or datetime.now(timezone.utc))
    sandbox = store.resolve_isolated_paper_sandbox(sandbox_id, now=evaluated)
    kill = store.isolated_paper_runtime_kill_switch(sandbox_id)
    configuration_entry = sandbox.get("effective_configuration")
    configuration = (
        configuration_entry.get("configuration", {})
        if isinstance(configuration_entry, Mapping) else {}
    )
    symbols = tuple(str(item).upper() for item in configuration.get("symbols", []))
    timeframe = str(configuration.get("timeframe", "1h"))
    interval = timeframe_duration(timeframe)
    closed_boundary, per_asset_boundary = latest_synchronized_closed_boundary(
        store, symbols, timeframe, observed_at=evaluated
    ) if symbols else (None, {})
    cycles = store.list_isolated_paper_runtime_cycles(sandbox_id, limit=10000)
    committed = [item for item in cycles if item["status"] == "COMMITTED"]
    current_cycle = committed[0] if committed else None
    previous_cycle = committed[1] if len(committed) > 1 else None
    current_result = (
        store.get_isolated_paper_ledger_result(current_cycle["result_id"])
        if current_cycle else None
    )
    previous_result = (
        store.get_isolated_paper_ledger_result(previous_cycle["result_id"])
        if previous_cycle else None
    )
    current_boundary = (
        _parse(str(current_cycle["snapshot_boundary"])) if current_cycle else None
    )
    new_closed_bar = closed_boundary is not None and (
        current_boundary is None or closed_boundary > current_boundary
    )
    alerts: list[dict[str, str]] = []
    if sandbox["effective_state"] != "ACTIVE":
        alerts.append(_alert(
            "CONFIGURATION_NOT_EFFECTIVE", "CRITICAL", sandbox_id,
            sandbox["blocking_reason"], "Forward bots have no configuration authority.",
            "Restore a separately approved effective PAPER_ONLY configuration.",
        ))
    if kill["effective_state"] != "CLEAR":
        alerts.append(_alert(
            "KILL_SWITCH_ARMED", "CRITICAL", sandbox_id,
            kill["blocking_reason"], "Every forward wake is blocked.",
            "Review the stop cause; clear locally only after prerequisites pass.",
        ))
    missing_assets = [symbol for symbol, value in per_asset_boundary.items() if value is None]
    if missing_assets:
        alerts.append(_alert(
            "CLOSED_CANDLE_MISSING", "CRITICAL", ",".join(missing_assets),
            "No fully closed stored candle is available.",
            "A synchronized bot cycle cannot be formed.",
            "Repair public-data ingestion and wait for a complete closed bar.",
        ))
    if closed_boundary is not None:
        lag = evaluated - (closed_boundary + interval)
        if lag >= interval * stale_closed_bars:
            alerts.append(_alert(
                "CLOSED_CANDLE_STALE", "CRITICAL", sandbox_id,
                f"Latest synchronized close is {lag.total_seconds():.0f} seconds old.",
                "Forward results no longer represent the current closed market state.",
                "Repair ingestion before running another bot cycle.",
            ))
    reserved = [item for item in cycles if item["status"] == "RESERVED"]
    for item in reserved:
        age = evaluated - _parse(str(item["reserved_at"]))
        if age > reserved_timeout:
            alerts.append(_alert(
                "CHECKPOINT_RESERVED_TOO_LONG", "CRITICAL", str(item["cycle_id"]),
                f"Checkpoint has remained RESERVED for {age.total_seconds():.0f} seconds.",
                "A prior worker may have crashed before atomic commit.",
                "Let its lease expire, verify authority and use the bounded recovery wake.",
            ))
    if current_cycle and current_result is None:
        alerts.append(_alert(
            "COMMITTED_RESULT_MISSING", "CRITICAL", str(current_cycle["cycle_id"]),
            "A COMMITTED checkpoint has no readable result.",
            "Bot account and delta evidence cannot be trusted.",
            "Preserve the database and restore from a verified backup.",
        ))
    elif current_result is not None and not verify_runtime_paper_ledger(current_result):
        alerts.append(_alert(
            "LEDGER_INTEGRITY_FAILED", "CRITICAL", str(current_result.get("result_id")),
            "The latest ledger or fleet hash failed verification.",
            "No bot account result is trusted.",
            "Preserve evidence and restore a verified database copy.",
        ))
    if previous_result is not None and not verify_runtime_paper_ledger(previous_result):
        alerts.append(_alert(
            "PREVIOUS_LEDGER_INTEGRITY_FAILED", "CRITICAL",
            str(previous_result.get("result_id")),
            "The prior ledger required for cycle delta failed verification.",
            "Cycle-to-cycle account changes cannot be trusted.",
            "Preserve evidence and restore a verified database copy.",
        ))
    for newer, older in zip(committed[:-1], committed[1:]):
        if newer.get("previous_committed_cycle_id") != older.get("cycle_id"):
            alerts.append(_alert(
                "CYCLE_LINEAGE_BROKEN", "CRITICAL", str(newer.get("cycle_id")),
                "The committed checkpoint does not reference the next older cycle.",
                "Burn-in continuity and account deltas are untrusted.",
                "Preserve the database and restore verified checkpoint lineage.",
            ))
            break
        gap = _parse(str(newer["snapshot_boundary"])) - _parse(
            str(older["snapshot_boundary"])
        )
        if gap > interval * 2:
            alerts.append(_alert(
                "BURN_IN_CADENCE_GAP", "HIGH", str(newer.get("cycle_id")),
                f"Committed boundaries are separated by {gap.total_seconds():.0f} seconds.",
                "The continuous burn-in suffix resets after this gap.",
                "Restore hourly closed-bar scheduling and rebuild a continuous suffix.",
            ))
            break
    current_bots = _bot_map(current_result)
    for bot_id, bot in current_bots.items():
        if bot.get("state") == "FROZEN":
            alerts.append(_alert(
                "BOT_RISK_FROZEN", "HIGH", bot_id,
                ",".join(bot.get("stop_reasons", [])) or "Approved risk stop triggered.",
                "The affected virtual account accepts no later strategy actions.",
                "Keep it frozen and review a separately approved configuration.",
            ))
    if current_cycle:
        for asset in current_cycle["snapshot"].get("assets", []):
            coverage = asset.get("funding_coverage", {})
            if coverage.get("status") != "COMPLETE":
                alerts.append(_alert(
                    "FUNDING_COVERAGE_GAP", "CRITICAL", str(asset.get("symbol")),
                    f"Funding coverage is {coverage.get('status', 'UNKNOWN')}.",
                    "Funding-dependent bot costs may be understated.",
                    "Backfill funding and cadence evidence before another cycle.",
                ))
    if new_closed_bar and not any(item["code"] == "CLOSED_CANDLE_STALE" for item in alerts):
        alerts.append(_alert(
            "NEW_CLOSED_BAR_PENDING", "INFO", sandbox_id,
            f"A new synchronized closed boundary {closed_boundary.isoformat()} is available.",
            "One idempotent forward bot wake is due.",
            "Run one bounded PAPER_ONLY forward wake.",
        ))
    boundaries = [_parse(str(item["snapshot_boundary"])) for item in committed]
    burn_in = calculate_continuous_burn_in(
        boundaries,
        interval=interval,
        minimum_days=minimum_burn_in_days,
        target_days=target_burn_in_days,
    )
    if burn_in["status"] != "TARGET_14D_REACHED":
        alerts.append(_alert(
            "BURN_IN_INCOMPLETE", "INFO", sandbox_id,
            f"Continuous evidence covers {burn_in['observed_days']:.2f} days.",
            "Long-running readiness is not yet established.",
            f"Continue closed-bar cycles through at least {target_burn_in_days} days.",
        ))
    blocking = any(item["severity"] == "CRITICAL" for item in alerts)
    high = any(item["severity"] == "HIGH" for item in alerts)
    status = (
        "BLOCKED" if blocking else
        "ALERT" if high else
        "RUN_REQUIRED" if new_closed_bar else
        "WAITING_FOR_NEW_CLOSED_BAR"
    )
    report = {
        "schema_version": FORWARD_OPS_SCHEMA_VERSION,
        "execution_mode": EXECUTION_MODE,
        "evaluated_at": evaluated.isoformat(),
        "sandbox_id": sandbox_id,
        "status": status,
        "trigger": {
            "timeframe": timeframe,
            "interval_seconds": interval.total_seconds(),
            "latest_synchronized_closed_boundary": (
                closed_boundary.isoformat() if closed_boundary else None
            ),
            "per_asset_closed_boundary": {
                symbol: value.isoformat() if value else None
                for symbol, value in per_asset_boundary.items()
            },
            "latest_committed_boundary": (
                current_boundary.isoformat() if current_boundary else None
            ),
            "new_closed_bar": new_closed_bar,
        },
        "latest_cycle": current_cycle,
        "cycle_delta": build_cycle_account_deltas(current_result, previous_result),
        "burn_in": burn_in,
        "alerts": alerts,
        "alert_counts": {
            severity: sum(item["severity"] == severity for item in alerts)
            for severity in ("CRITICAL", "HIGH", "INFO")
        },
        "authority": {
            "stored_public_market_data_only": True,
            "closed_candles_only": True,
            "read_only_view": True,
            "browser_control_allowed": False,
            "external_order_requests_created": False,
            "order_path_present": False,
            "live_execution_allowed": False,
        },
    }
    report["report_sha256"] = canonical_sha256(report)
    return report


def verify_forward_bot_operations_view(report: Mapping[str, Any]) -> bool:
    if report.get("schema_version") != FORWARD_OPS_SCHEMA_VERSION:
        return False
    if report.get("execution_mode") != EXECUTION_MODE:
        return False
    if report.get("authority") != {
        "stored_public_market_data_only": True,
        "closed_candles_only": True,
        "read_only_view": True,
        "browser_control_allowed": False,
        "external_order_requests_created": False,
        "order_path_present": False,
        "live_execution_allowed": False,
    }:
        return False
    unhashed = dict(report)
    supplied = unhashed.pop("report_sha256", None)
    return supplied == canonical_sha256(unhashed)


def run_forward_bot_wake(
    store: MarketStore,
    sandbox_id: str,
    *,
    worker_id: str = "aars-forward-bot-worker",
    lease_seconds: int = 120,
    now: datetime | None = None,
    token_factory: Callable[[], str] | None = None,
) -> dict[str, Any]:
    evaluated = _utc(now or datetime.now(timezone.utc))
    before = build_forward_bot_operations_view(store, sandbox_id, now=evaluated)
    critical_codes = {
        item["code"] for item in before["alerts"]
        if item["severity"] == "CRITICAL"
    }
    recoverable_reserved_only = bool(critical_codes) and critical_codes <= {
        "CHECKPOINT_RESERVED_TOO_LONG"
    }
    if before["status"] == "BLOCKED" and not recoverable_reserved_only:
        status = "BLOCKED"
        runtime = None
    elif not before["trigger"]["new_closed_bar"]:
        status = "WAITING_NO_NEW_CLOSED_BAR"
        runtime = None
    else:
        clock = lambda: evaluated
        kwargs: dict[str, Any] = {}
        if token_factory is not None:
            kwargs["token_factory"] = token_factory
        try:
            runtime = run_isolated_paper_runtime(
                store,
                sandbox_id,
                worker_id=worker_id,
                settings=IsolatedRuntimeSettings(
                    lease_seconds=lease_seconds,
                    heartbeat_interval_seconds=max(1.0, min(30.0, lease_seconds / 3)),
                    max_cycles=1,
                ),
                clock=clock,
                **kwargs,
            )
            paper = runtime["cycles"][0].get("paper_cycle", {}) if runtime["cycles"] else {}
            status = str(paper.get("status", "BLOCKED"))
        except ValueError as exc:
            runtime = None
            status = (
                "SKIPPED_CONCURRENT_WAKE"
                if "already has a running leased session" in str(exc)
                else "BLOCKED"
            )
    after = build_forward_bot_operations_view(store, sandbox_id, now=evaluated)
    return {
        "schema_version": FORWARD_WAKE_SCHEMA_VERSION,
        "execution_mode": EXECUTION_MODE,
        "evaluated_at": evaluated.isoformat(),
        "sandbox_id": sandbox_id,
        "worker_id": worker_id,
        "status": status,
        "cycle_executed": runtime is not None,
        "runtime": runtime,
        "operations": after,
        "authority": {
            "closed_candle_trigger_only": True,
            "bounded_lease_only": True,
            "public_market_ingestion_started": False,
            "external_order_requests_created": False,
            "order_path_present": False,
            "live_execution_allowed": False,
        },
    }


def run_forward_bot_scheduler(
    store: MarketStore,
    sandbox_id: str,
    *,
    poll_seconds: float = 60.0,
    max_wakes: int | None = 1,
    worker_id: str = "aars-forward-bot-worker",
    lease_seconds: int = 120,
    clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    sleeper: Callable[[float], None] = time.sleep,
    on_wake: Callable[[dict[str, Any]], None] | None = None,
) -> list[dict[str, Any]]:
    if poll_seconds <= 0:
        raise ValueError("poll_seconds must be positive")
    if max_wakes is not None and max_wakes <= 0:
        raise ValueError("max_wakes must be positive when supplied")
    wakes = []
    while max_wakes is None or len(wakes) < max_wakes:
        wake = run_forward_bot_wake(
            store,
            sandbox_id,
            worker_id=worker_id,
            lease_seconds=lease_seconds,
            now=clock(),
        )
        wakes.append(wake)
        if on_wake is not None:
            on_wake(wake)
        if max_wakes is not None and len(wakes) >= max_wakes:
            break
        sleeper(poll_seconds)
    return wakes
