from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime, timezone
from math import isfinite
from typing import Any, Iterable

from .service import WINDOWS
from .shadow import SNAPSHOT_SCHEMA_VERSION, _promotion_evidence_eligible
from .simulation import AarsDynamicStrategy, BuyAndHoldStrategy, ReplayEngine, ReplayResult
from .storage import MarketStore


SCHEMA_VERSION = "mil3.strategy-diagnostics.v1"
EXECUTION_MODE = "PAPER_ONLY"
_STATE_PATTERN = re.compile(r"(?:^|;)\s*state=([A-Z_]+)")


def _utc(value: str | datetime) -> datetime:
    parsed = datetime.fromisoformat(value) if isinstance(value, str) else value
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _empty(reason: str, *, snapshot_id: str | None = None) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "execution_mode": EXECUTION_MODE,
        "read_only": True,
        "status": "DEGRADED",
        "data_trust": {
            "status": "UNAVAILABLE",
            "reason": reason,
            "source_snapshot_id": snapshot_id,
        },
        "authority": {
            "automatic_strategy_change_allowed": False,
            "paper_configuration_activation_allowed": False,
            "live_execution_allowed": False,
        },
        "assets": [],
        "attribution": None,
        "findings": [],
    }


def _select_snapshot(
    store: MarketStore, snapshot_id: str | None
) -> tuple[str, dict[str, Any]] | None:
    if snapshot_id:
        payload = store.get_shadow_daily_snapshot(snapshot_id)
        return (snapshot_id, payload) if payload is not None else None
    for candidate_id, payload in reversed(
        store.load_shadow_daily_snapshots(limit=90, target_strategy="AARS_DYNAMIC")
    ):
        if _promotion_evidence_eligible(payload):
            return candidate_id, payload
    return None


def _direction(exposure: float, *, epsilon: float = 1e-9) -> str:
    if exposure > epsilon:
        return "LONG"
    if exposure < -epsilon:
        return "TACTICAL_SHORT"
    return "FLAT"


def _bucket_attribution(result: ReplayResult) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    direction: dict[str, dict[str, float]] = defaultdict(
        lambda: {"bars": 0, "equity_change": 0.0, "turnover": 0.0, "fees": 0.0, "slippage": 0.0}
    )
    regime: dict[str, dict[str, float]] = defaultdict(
        lambda: {"bars": 0, "equity_change": 0.0, "turnover": 0.0, "fees": 0.0, "slippage": 0.0}
    )
    fills_by_index: dict[int, list[Any]] = defaultdict(list)
    regime_by_index: dict[int, str] = {}
    for fill in result.fills:
        fills_by_index[fill.index].append(fill)
        match = _STATE_PATTERN.search(fill.reason)
        if match:
            regime_by_index[fill.index] = match.group(1)

    previous_equity = result.summary.initial_equity
    previous_regime = "UNKNOWN"
    for point in result.trace:
        label = _direction(point.net_exposure)
        matched_regime = regime_by_index.get(point.index, previous_regime)
        if matched_regime != "UNKNOWN":
            previous_regime = matched_regime
        delta = point.equity - previous_equity
        previous_equity = point.equity
        direction[label]["bars"] += 1
        direction[label]["equity_change"] += delta
        regime[matched_regime]["bars"] += 1
        regime[matched_regime]["equity_change"] += delta
        for fill in fills_by_index.get(point.index, ()):
            for bucket in (direction[label], regime[matched_regime]):
                bucket["turnover"] += fill.notional
                bucket["fees"] += fill.fee
                bucket["slippage"] += fill.slippage_cost

    def rows(values: dict[str, dict[str, float]], label: str) -> list[dict[str, Any]]:
        return sorted(
            ({label: key, **value} for key, value in values.items()),
            key=lambda item: (item["equity_change"], item[label]),
        )

    return rows(direction, "direction"), rows(regime, "regime")


def _reversals(result: ReplayResult) -> int:
    signs = [_direction(point.net_exposure) for point in result.trace]
    directional = [item for item in signs if item != "FLAT"]
    return sum(before != after for before, after in zip(directional, directional[1:]))


def _sum(rows: Iterable[dict[str, Any]], key: str) -> float:
    return sum(float(row[key]) for row in rows)


def build_strategy_diagnostics(
    store: MarketStore,
    *,
    snapshot_id: str | None = None,
) -> dict[str, Any]:
    """Explain one immutable v2 AARS snapshot using the shared replay ledger."""
    selected = _select_snapshot(store, snapshot_id)
    if selected is None:
        reason = "SNAPSHOT_NOT_FOUND" if snapshot_id else "NO_ELIGIBLE_V2_STABLE_SNAPSHOT"
        return _empty(reason, snapshot_id=snapshot_id)
    source_id, snapshot = selected
    if not _promotion_evidence_eligible(snapshot):
        return _empty("SNAPSHOT_NOT_ELIGIBLE_V2_EVIDENCE", snapshot_id=source_id)
    if snapshot.get("configuration", {}).get("portfolio_strategy") != "AARS_DYNAMIC":
        return _empty("SNAPSHOT_PORTFOLIO_STRATEGY_NOT_AARS_DYNAMIC", snapshot_id=source_id)

    configuration = snapshot["configuration"]
    as_of = _utc(snapshot["as_of"])
    timeframe = str(configuration["timeframe"])
    replay_window = str(configuration["replay_window"])
    duration = WINDOWS.get(replay_window)
    if replay_window not in WINDOWS:
        return _empty("UNSUPPORTED_ARCHIVED_REPLAY_WINDOW", snapshot_id=source_id)
    start = as_of - duration if duration is not None else None
    warmup_bars = int(configuration["warmup_bars"])
    archived_assets = {
        str(item["symbol"]): item for item in snapshot["portfolio"]["assets"]
    }
    weights = {
        str(symbol): float(weight)
        for symbol, weight in snapshot["portfolio"]["weights"].items()
    }

    assets: list[dict[str, Any]] = []
    replayed_aars: dict[str, ReplayResult] = {}
    verification_failures: list[str] = []
    for symbol in snapshot["symbols"]:
        candles = store.load_candles(symbol, timeframe, start=start, end=as_of)
        if not candles or candles[-1].open_time != as_of or len(candles) <= warmup_bars:
            verification_failures.append(f"{symbol}:EVIDENCE_BOUNDARY_UNAVAILABLE")
            continue
        funding = store.load_funding_rates(
            symbol, start=candles[0].open_time, end=as_of
        )
        engine = ReplayEngine(funding_rates=funding)
        aars = engine.run_detailed(
            candles, AarsDynamicStrategy(max_abs_exposure=1.0), warmup_bars=warmup_bars
        )
        replayed_aars[symbol] = aars
        buy_hold = engine.run_detailed(
            candles, BuyAndHoldStrategy(), warmup_bars=warmup_bars
        )
        archived_return = float(archived_assets[symbol]["total_return"])
        return_error = abs(aars.summary.total_return - archived_return)
        if return_error > 1e-10:
            verification_failures.append(f"{symbol}:ARCHIVED_RETURN_MISMATCH")

        directions, regimes = _bucket_attribution(aars)
        costs = {
            "fees": aars.summary.fees,
            "slippage": aars.summary.slippage,
            "funding": aars.summary.funding,
        }
        total_cost = sum(costs.values())
        weight = weights[symbol]
        assets.append(
            {
                "symbol": symbol,
                "weight": weight,
                "source_verification": {
                    "status": "PASS" if return_error <= 1e-10 else "FAIL",
                    "archived_total_return": archived_return,
                    "replayed_total_return": aars.summary.total_return,
                    "absolute_error": return_error,
                },
                "performance": {
                    "aars_total_return": aars.summary.total_return,
                    "buy_hold_total_return": buy_hold.summary.total_return,
                    "return_gap_vs_buy_hold": (
                        aars.summary.total_return - buy_hold.summary.total_return
                    ),
                    "weighted_gap_contribution": weight * (
                        aars.summary.total_return - buy_hold.summary.total_return
                    ),
                    "max_drawdown": aars.summary.max_drawdown,
                    "sharpe": aars.summary.sharpe_approx,
                    "sortino": aars.summary.sortino,
                    "profit_factor": (
                        aars.summary.profit_factor
                        if isfinite(aars.summary.profit_factor)
                        else None
                    ),
                },
                "costs": {
                    **costs,
                    "total_modeled_cost": total_cost,
                    "cost_drag_return": total_cost / aars.summary.initial_equity,
                    "accounting_cost_reversal_return": (
                        aars.summary.total_return
                        + total_cost / aars.summary.initial_equity
                    ),
                    "counterfactual_kind": "ACCOUNTING_ADD_BACK_NOT_EXECUTION_FORECAST",
                },
                "activity": {
                    "fills": len(aars.fills),
                    "turnover_notional": aars.summary.turnover_notional,
                    "turnover_multiple": (
                        aars.summary.turnover_notional / aars.summary.initial_equity
                    ),
                    "direction_reversals": _reversals(aars),
                },
                "risk": {
                    "max_abs_net_exposure": aars.summary.max_abs_net_exposure,
                    "max_effective_leverage": aars.summary.max_effective_leverage,
                    "min_margin_buffer_pct": aars.summary.min_margin_buffer_pct,
                    "max_liquidation_risk": aars.summary.max_liquidation_risk,
                    "liquidation_events": aars.summary.liquidation_events,
                },
                "direction_attribution": directions,
                "regime_attribution": regimes,
            }
        )

    if not verification_failures:
        archived_trace = snapshot["portfolio"].get("trace", ())
        if not archived_trace:
            verification_failures.append("ARCHIVED_PORTFOLIO_TRACE_MISSING")
        trace_by_symbol = {
            symbol: {point.as_of: point for point in result.trace}
            for symbol, result in replayed_aars.items()
        }
        for archived_point in archived_trace:
            as_of_key = str(archived_point["as_of"])
            try:
                points = {
                    symbol: trace_by_symbol[symbol][as_of_key]
                    for symbol in snapshot["symbols"]
                }
            except KeyError:
                verification_failures.append("PORTFOLIO_TRACE_BOUNDARY_MISMATCH")
                break
            equity_index = sum(
                weights[symbol]
                * points[symbol].equity
                / replayed_aars[symbol].summary.initial_equity
                for symbol in snapshot["symbols"]
            )
            net_exposure = sum(
                weights[symbol] * points[symbol].net_exposure
                for symbol in snapshot["symbols"]
            )
            if (
                abs(equity_index - float(archived_point["equity_index"])) > 1e-10
                or abs(net_exposure - float(archived_point["net_exposure"])) > 1e-10
            ):
                verification_failures.append("ARCHIVED_PORTFOLIO_TRACE_MISMATCH")
                break

    if verification_failures:
        payload = _empty(";".join(verification_failures), snapshot_id=source_id)
        payload["assets"] = assets
        return payload

    portfolio_aars_return = _sum(
        ({"value": item["weight"] * item["performance"]["aars_total_return"]} for item in assets),
        "value",
    )
    portfolio_buy_hold_return = _sum(
        ({"value": item["weight"] * item["performance"]["buy_hold_total_return"]} for item in assets),
        "value",
    )
    weighted_cost_drag = _sum(
        ({"value": item["weight"] * item["costs"]["cost_drag_return"]} for item in assets),
        "value",
    )
    worst_asset = min(assets, key=lambda item: item["performance"]["weighted_gap_contribution"])
    all_directions = [
        {"symbol": item["symbol"], **row}
        for item in assets
        for row in item["direction_attribution"]
    ]
    all_regimes = [
        {"symbol": item["symbol"], **row}
        for item in assets
        for row in item["regime_attribution"]
    ]
    worst_direction = min(all_directions, key=lambda item: item["equity_change"])
    worst_regime = min(all_regimes, key=lambda item: item["equity_change"])
    cost_components = {
        key: sum(item["weight"] * item["costs"][key] for item in assets)
        for key in ("fees", "slippage", "funding")
    }
    largest_cost = max(cost_components, key=lambda key: abs(cost_components[key]))
    latest_raw = {
        symbol: (
            store.latest_open_time(symbol, timeframe).isoformat()
            if store.latest_open_time(symbol, timeframe) is not None
            else None
        )
        for symbol in snapshot["symbols"]
    }
    findings = [
        {
            "kind": "EVIDENCE",
            "code": "BASELINE_GAP",
            "severity": "HIGH" if portfolio_aars_return < portfolio_buy_hold_return else "NORMAL",
            "statement": "Observed equal-weight AARS return gap versus Buy & Hold.",
            "value": portfolio_aars_return - portfolio_buy_hold_return,
            "requires_challenger_test": False,
        },
        {
            "kind": "EVIDENCE",
            "code": "HIGHEST_ASSET_DRAG",
            "severity": "HIGH" if worst_asset["performance"]["weighted_gap_contribution"] < 0 else "NORMAL",
            "statement": f"{worst_asset['symbol']} is the largest weighted asset gap contributor.",
            "value": worst_asset["performance"]["weighted_gap_contribution"],
            "requires_challenger_test": False,
        },
        {
            "kind": "HYPOTHESIS",
            "code": "TEST_COST_AND_TURNOVER_CHALLENGER",
            "severity": "ELEVATED" if weighted_cost_drag > 0 else "NORMAL",
            "statement": "Test a lower-turnover challenger; do not change the active PAPER_ONLY configuration from this diagnostic.",
            "value": weighted_cost_drag,
            "requires_challenger_test": True,
        },
        {
            "kind": "HYPOTHESIS",
            "code": "TEST_WORST_REGIME_DIRECTION_FILTER",
            "severity": "ELEVATED",
            "statement": (
                f"Test bounded exposure changes for {worst_regime['regime']} / "
                f"{worst_direction['direction']} in an isolated challenger replay."
            ),
            "value": min(worst_regime["equity_change"], worst_direction["equity_change"]),
            "requires_challenger_test": True,
        },
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "execution_mode": EXECUTION_MODE,
        "read_only": True,
        "status": "READY",
        "data_trust": {
            "status": "VERIFIED",
            "reason": "REPLAY_MATCHES_IMMUTABLE_V2_ASSET_RETURNS_AND_PORTFOLIO_TRACE",
            "source_snapshot_id": source_id,
            "source_schema_version": SNAPSHOT_SCHEMA_VERSION,
            "stable_as_of": as_of.isoformat(),
            "latest_raw_open_time": latest_raw,
            "fully_closed": True,
        },
        "authority": {
            "automatic_strategy_change_allowed": False,
            "paper_configuration_activation_allowed": False,
            "live_execution_allowed": False,
        },
        "configuration": {
            "symbols": list(snapshot["symbols"]),
            "timeframe": timeframe,
            "replay_window": replay_window,
            "warmup_bars": warmup_bars,
            "capital_model": snapshot["portfolio"]["capital_model"],
            "parameter_policy": configuration["portfolio_parameter_policy"],
        },
        "attribution": {
            "aars_total_return": portfolio_aars_return,
            "buy_hold_total_return": portfolio_buy_hold_return,
            "return_gap_vs_buy_hold": portfolio_aars_return - portfolio_buy_hold_return,
            "weighted_cost_drag_return": weighted_cost_drag,
            "accounting_cost_reversal_return": portfolio_aars_return + weighted_cost_drag,
            "cost_components": cost_components,
            "largest_cost_component": largest_cost,
            "highest_asset_drag": worst_asset["symbol"],
            "worst_direction": {
                "symbol": worst_direction["symbol"],
                "direction": worst_direction["direction"],
                "equity_change": worst_direction["equity_change"],
            },
            "worst_regime": {
                "symbol": worst_regime["symbol"],
                "regime": worst_regime["regime"],
                "equity_change": worst_regime["equity_change"],
            },
            "limitations": [
                "Attribution groups accounting changes; it does not establish causal alpha.",
                "Cost reversal adds modeled charges back and is not an execution forecast.",
                "Optimization findings cannot activate or modify any PAPER_ONLY configuration.",
            ],
        },
        "assets": assets,
        "findings": findings,
    }
