from __future__ import annotations

import math
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from statistics import fmean
from typing import Any, Mapping, Sequence

from .isolated_config import canonical_sha256
from .models import Candle, FundingRate
from .simulation import (
    AarsDynamicStrategy,
    BuyAndHoldStrategy,
    LeveragedFuturesLongGridStrategy,
    ReplayEngine,
    ReplayResult,
    RiskStopPolicy,
    ShadowStrategy,
    SpotGridStrategy,
)
from .validation import ValidationCandidate


EXECUTION_MODE = "PAPER_ONLY"
BOT_FLEET_SCHEMA_VERSION = "mil3.shadow-strategy-bot-fleet.v1"
BOT_ORDER = ("BUY_HOLD", "SPOT_GRID", "FUTURES_LONG_GRID", "AARS_DYNAMIC")


@dataclass(frozen=True)
class ShadowBotAssetInput:
    symbol: str
    input_sha256: str
    candles: tuple[Candle, ...]
    funding: tuple[FundingRate, ...]


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _finite(value: float | int | str | None) -> float | int | str | None:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _summary(result: ReplayResult) -> dict[str, Any]:
    return {key: _finite(value) for key, value in result.summary.as_dict().items()}


def _mean(values: Sequence[float | None]) -> float | None:
    finite = [float(value) for value in values if value is not None and math.isfinite(value)]
    return fmean(finite) if finite else None


def _extreme(
    values: Sequence[float | None], *, highest: bool
) -> float | None:
    finite = [float(value) for value in values if value is not None and math.isfinite(value)]
    if not finite:
        return None
    return max(finite) if highest else min(finite)


def _aggregate(ledgers: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "asset_count": len(ledgers),
        "initial_equity": sum(float(item["initial_equity"]) for item in ledgers),
        "final_equity": sum(float(item["final_equity"]) for item in ledgers),
        "mean_total_return": _mean([item.get("total_return") for item in ledgers]),
        "worst_max_drawdown": max(float(item["max_drawdown"]) for item in ledgers),
        "mean_sharpe_approx": _mean([item.get("sharpe_approx") for item in ledgers]),
        "mean_sortino": _mean([item.get("sortino") for item in ledgers]),
        "mean_profit_factor": _mean([item.get("profit_factor") for item in ledgers]),
        "turnover_notional": sum(float(item["turnover_notional"]) for item in ledgers),
        "fees": sum(float(item["fees"]) for item in ledgers),
        "slippage": sum(float(item["slippage"]) for item in ledgers),
        "funding": sum(float(item["funding"]) for item in ledgers),
        "realized_pnl": sum(float(item["realized_pnl"]) for item in ledgers),
        "realized_grid_pnl": sum(float(item["realized_grid_pnl"]) for item in ledgers),
        "inventory_unrealized_pnl": sum(
            float(item["inventory_unrealized_pnl"]) for item in ledgers
        ),
        "mean_final_net_exposure": _mean(
            [item.get("final_net_exposure") for item in ledgers]
        ),
        "max_abs_net_exposure": max(
            float(item["max_abs_net_exposure"]) for item in ledgers
        ),
        "mean_final_effective_leverage": _mean(
            [item.get("final_effective_leverage") for item in ledgers]
        ),
        "max_effective_leverage": _extreme(
            [item.get("max_effective_leverage") for item in ledgers], highest=True
        ),
        "min_margin_buffer_pct": _extreme(
            [item.get("min_margin_buffer_pct") for item in ledgers], highest=False
        ),
        "max_liquidation_risk": _extreme(
            [item.get("max_liquidation_risk") for item in ledgers], highest=True
        ),
        "liquidation_events": sum(int(item["liquidation_events"]) for item in ledgers),
    }


def _strategy(bot_id: str, candidate: ValidationCandidate) -> ShadowStrategy:
    if bot_id == "BUY_HOLD":
        return BuyAndHoldStrategy()
    if bot_id == "SPOT_GRID":
        return SpotGridStrategy(
            spacing_pct=candidate.grid_spacing_pct,
            levels=candidate.grid_levels,
        )
    if bot_id == "FUTURES_LONG_GRID":
        return LeveragedFuturesLongGridStrategy(
            max_leverage=candidate.futures_leverage,
            spacing_pct=candidate.grid_spacing_pct,
            levels=candidate.grid_levels,
            tactical_hedge=candidate.tactical_hedge,
        )
    if bot_id == "AARS_DYNAMIC":
        return AarsDynamicStrategy(
            max_abs_exposure=candidate.aars_max_abs_exposure
        )
    raise ValueError(f"unsupported shadow bot: {bot_id}")


def _strategy_configuration(
    bot_id: str, candidate: ValidationCandidate
) -> dict[str, Any]:
    if bot_id == "BUY_HOLD":
        return {"strategy": bot_id, "max_leverage": 1.0}
    if bot_id == "SPOT_GRID":
        return {
            "strategy": bot_id,
            "max_leverage": 1.0,
            "grid_spacing_pct": candidate.grid_spacing_pct,
            "grid_levels": candidate.grid_levels,
        }
    if bot_id == "FUTURES_LONG_GRID":
        return {
            "strategy": bot_id,
            "exchange_leverage_parameter": candidate.futures_leverage,
            "grid_spacing_pct": candidate.grid_spacing_pct,
            "grid_levels": candidate.grid_levels,
            "tactical_hedge": candidate.tactical_hedge,
        }
    return {
        "strategy": bot_id,
        "max_abs_exposure": candidate.aars_max_abs_exposure,
        "long_flat_tactical_short": True,
    }


def _account(result: ReplayResult) -> dict[str, Any]:
    point = result.trace[-1]
    latest_fill = asdict(result.fills[-1]) if result.fills else None
    categories = Counter(fill.category for fill in result.fills)
    return {
        "as_of": point.as_of,
        "mark_price": point.mark_price,
        "equity": point.equity,
        "position_qty": point.position_qty,
        "avg_entry": point.avg_entry,
        "realized_pnl": point.realized_pnl,
        "unrealized_pnl": point.unrealized_pnl,
        "fees": point.fees,
        "funding": point.funding,
        "net_exposure": point.net_exposure,
        "effective_leverage": _finite(point.effective_leverage),
        "margin_buffer_pct": _finite(point.margin_buffer_pct),
        "liquidation_risk": _finite(point.liquidation_risk),
        "fill_evidence": {
            "simulated_fill_count": len(result.fills),
            "categories": dict(sorted(categories.items())),
            "latest_simulated_fill": latest_fill,
        },
    }


def calculate_shadow_bot_fleet(
    asset_inputs: Sequence[ShadowBotAssetInput],
    *,
    cycle_id: str,
    snapshot_sha256: str,
    configuration_sha256: str,
    candidate: ValidationCandidate,
    settings: Mapping[str, Any],
    warmup_bars: int,
    calculated_at: datetime,
) -> dict[str, Any]:
    if not asset_inputs:
        raise ValueError("shadow bot fleet requires at least one asset")
    risk_policy = RiskStopPolicy(
        max_drawdown=float(settings["stop_max_drawdown"]),
        max_liquidation_risk=float(settings["stop_max_liquidation_risk"]),
        liquidation_events_allowed=0,
    )
    bots: list[dict[str, Any]] = []
    for bot_id in BOT_ORDER:
        per_asset = []
        for asset in asset_inputs:
            result = ReplayEngine(
                initial_equity=float(settings["initial_equity_per_asset"]),
                fee_rate=float(settings["fee_rate"]),
                slippage_rate=float(settings["slippage_rate"]),
                funding_rates=asset.funding,
                maintenance_margin_rate=float(settings["maintenance_margin_rate"]),
            ).run_detailed(
                asset.candles,
                _strategy(bot_id, candidate),
                warmup_bars=warmup_bars,
                risk_stop_policy=risk_policy,
            )
            per_asset.append({
                "symbol": asset.symbol,
                "input_sha256": asset.input_sha256,
                "ledger": _summary(result),
                "account": _account(result),
                "risk": {
                    "state": result.risk_state,
                    "stop_reasons": list(result.risk_stop_reasons),
                    "stopped_at": result.risk_stopped_at,
                },
            })
        ledgers = [item["ledger"] for item in per_asset]
        stopped_assets = [
            item for item in per_asset if item["risk"]["state"] == "FROZEN"
        ]
        stop_reasons = sorted({
            reason
            for item in stopped_assets
            for reason in item["risk"]["stop_reasons"]
        })
        bots.append({
            "bot_id": bot_id,
            "account_id": f"{configuration_sha256[:16]}:{bot_id}",
            "configuration": _strategy_configuration(bot_id, candidate),
            "state": "FROZEN" if stopped_assets else "RUNNING",
            "stop_reasons": stop_reasons,
            "frozen_asset_count": len(stopped_assets),
            "aggregate": _aggregate(ledgers),
            "per_asset": per_asset,
        })
    risk_limits = {
        "max_drawdown": risk_policy.max_drawdown,
        "max_liquidation_risk": risk_policy.max_liquidation_risk,
        "liquidation_events_allowed": risk_policy.liquidation_events_allowed,
        "response": "FLATTEN_IF_SOLVENT_AND_FREEZE_AFFECTED_VIRTUAL_ACCOUNT",
    }
    deterministic = {
        "cycle_id": cycle_id,
        "snapshot_sha256": snapshot_sha256,
        "configuration_sha256": configuration_sha256,
        "capital_model": "independent equal-capital asset buckets per bot",
        "bot_order": list(BOT_ORDER),
        "risk_limits": risk_limits,
        "bots": bots,
    }
    payload = {
        "schema_version": BOT_FLEET_SCHEMA_VERSION,
        "execution_mode": EXECUTION_MODE,
        "fleet_id": canonical_sha256(deterministic)[:24],
        "calculated_at": _utc(calculated_at).isoformat(),
        **deterministic,
        "authority": {
            "independent_virtual_accounts": True,
            "simulated_order_intents_only": True,
            "risk_stop_can_freeze_paper_accounts_only": True,
            "external_order_requests_created": False,
            "order_path_present": False,
            "live_execution_allowed": False,
        },
    }
    payload["fleet_sha256"] = canonical_sha256(payload)
    return payload


def verify_shadow_bot_fleet(payload: Mapping[str, Any]) -> bool:
    if payload.get("schema_version") != BOT_FLEET_SCHEMA_VERSION:
        return False
    if payload.get("execution_mode") != EXECUTION_MODE:
        return False
    if payload.get("bot_order") != list(BOT_ORDER):
        return False
    if payload.get("authority") != {
        "independent_virtual_accounts": True,
        "simulated_order_intents_only": True,
        "risk_stop_can_freeze_paper_accounts_only": True,
        "external_order_requests_created": False,
        "order_path_present": False,
        "live_execution_allowed": False,
    }:
        return False
    if [item.get("bot_id") for item in payload.get("bots", [])] != list(BOT_ORDER):
        return False
    deterministic = {
        "cycle_id": payload.get("cycle_id"),
        "snapshot_sha256": payload.get("snapshot_sha256"),
        "configuration_sha256": payload.get("configuration_sha256"),
        "capital_model": payload.get("capital_model"),
        "bot_order": payload.get("bot_order"),
        "risk_limits": payload.get("risk_limits"),
        "bots": payload.get("bots"),
    }
    if payload.get("fleet_id") != canonical_sha256(deterministic)[:24]:
        return False
    unhashed = dict(payload)
    supplied = unhashed.pop("fleet_sha256", None)
    return supplied == canonical_sha256(unhashed)
