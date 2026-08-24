from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Sequence


def _strategy(payload: Mapping[str, Any], strategy_id: str) -> Mapping[str, Any]:
    for strategy in payload["strategies"]:
        if strategy["id"] == strategy_id:
            return strategy
    raise ValueError(f"strategy not found in asset payload: {strategy_id}")


def build_portfolio_payload(
    asset_payloads: Sequence[Mapping[str, Any]],
    *,
    strategy_id: str = "AARS_DYNAMIC",
    weights: Mapping[str, float] | None = None,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    if not asset_payloads:
        raise ValueError("asset_payloads must not be empty")
    symbols = [str(payload["market"]["symbol"]).upper() for payload in asset_payloads]
    if len(set(symbols)) != len(symbols):
        raise ValueError("asset payload symbols must be unique")
    raw_weights = {symbol: float((weights or {}).get(symbol, 1.0)) for symbol in symbols}
    if any(value < 0 for value in raw_weights.values()) or sum(raw_weights.values()) <= 0:
        raise ValueError("portfolio weights must be non-negative with a positive sum")
    total_weight = sum(raw_weights.values())
    normalized = {symbol: value / total_weight for symbol, value in raw_weights.items()}

    selected = {symbol: _strategy(payload, strategy_id) for symbol, payload in zip(symbols, asset_payloads)}
    traces = {
        symbol: {point["as_of"]: point for point in strategy["trace"]}
        for symbol, strategy in selected.items()
    }
    common_times = sorted(set.intersection(*(set(trace) for trace in traces.values())))
    if not common_times:
        raise ValueError("asset replay traces have no common timestamps")

    peak = 1.0
    max_drawdown = 0.0
    portfolio_trace: list[dict[str, Any]] = []
    for as_of in common_times:
        equity_index = 0.0
        net_exposure = 0.0
        gross_exposure = 0.0
        effective_leverage = 0.0
        min_margin_buffer = 1.0
        max_liquidation_risk = 0.0
        for symbol in symbols:
            point = traces[symbol][as_of]
            summary = selected[symbol]["summary"]
            weight = normalized[symbol]
            equity_index += weight * point["equity"] / summary["initial_equity"]
            net_exposure += weight * point["net_exposure"]
            gross_exposure += weight * abs(point["net_exposure"])
            effective_leverage += weight * (point["effective_leverage"] or 0.0)
            min_margin_buffer = min(min_margin_buffer, point["margin_buffer_pct"])
            max_liquidation_risk = max(max_liquidation_risk, point["liquidation_risk"])
        peak = max(peak, equity_index)
        drawdown = max(0.0, 1.0 - equity_index / peak) if peak > 0 else 1.0
        max_drawdown = max(max_drawdown, drawdown)
        portfolio_trace.append(
            {
                "as_of": as_of,
                "equity_index": equity_index,
                "drawdown": drawdown,
                "net_exposure": net_exposure,
                "gross_exposure": gross_exposure,
                "effective_leverage": effective_leverage,
                "min_margin_buffer_pct": min_margin_buffer,
                "max_liquidation_risk": max_liquidation_risk,
            }
        )

    final = portfolio_trace[-1]
    per_asset = []
    for payload, symbol in zip(asset_payloads, symbols):
        summary = selected[symbol]["summary"]
        per_asset.append(
            {
                "symbol": symbol,
                "weight": normalized[symbol],
                "freshness_status": payload["market"]["freshness_status"],
                "funding_coverage_status": payload["funding"]["coverage"]["status"],
                "funding_cadence_hours": payload["funding"]["coverage"].get("cadence_hours", 8),
                "funding_cadence_source": payload["funding"]["coverage"].get(
                    "cadence_source", "DEFAULT_8H_FALLBACK"
                ),
                "total_return": summary["total_return"],
                "final_net_exposure": summary["final_net_exposure"],
                "max_effective_leverage": summary["max_effective_leverage"],
                "max_liquidation_risk": summary["max_liquidation_risk"],
                "liquidation_events": summary["liquidation_events"],
            }
        )

    generated = generated_at or datetime.now(timezone.utc)
    degraded_assets = [
        item["symbol"]
        for item in per_asset
        if item["freshness_status"] != "CURRENT" or item["funding_coverage_status"] != "COMPLETE"
    ]
    return {
        "schema_version": "mil3.portfolio.v1",
        "generated_at": generated.astimezone(timezone.utc).isoformat(),
        "execution_mode": "PAPER_ONLY",
        "strategy": strategy_id,
        "capital_model": "independent equal-weight capital buckets; no exchange margin netting",
        "weights": normalized,
        "summary": {
            "total_return": final["equity_index"] - 1.0,
            "max_drawdown": max_drawdown,
            "final_net_exposure": final["net_exposure"],
            "final_gross_exposure": final["gross_exposure"],
            "final_effective_leverage": final["effective_leverage"],
            "min_margin_buffer_pct": min(point["min_margin_buffer_pct"] for point in portfolio_trace),
            "max_liquidation_risk": max(point["max_liquidation_risk"] for point in portfolio_trace),
            "liquidation_events": sum(item["liquidation_events"] for item in per_asset),
            "degraded": bool(degraded_assets),
            "degraded_assets": degraded_assets,
        },
        "assets": per_asset,
        "trace": portfolio_trace,
        "review_gate": {
            "disposition": "DEFER" if degraded_assets or any(item["liquidation_events"] for item in per_asset) else "ACCEPT_WITH_MONITORING",
            "live_execution_allowed": False,
        },
    }
