from __future__ import annotations

from typing import Any

import streamlit as st

from weather_dashboard.ui.compact_panel import render_kv_section, render_panel_title


def build_read_only_account_summary(
    snapshot: dict | None,
    selected_market_id: str | None,
    readiness_report: dict | None = None,
) -> dict:
    if not snapshot:
        return {
            "available": False,
            "manual_order_only": True,
            "snapshot_updated_at": "-",
            "source": "-",
            "account_id": "-",
            "available_balance": 0.0,
            "total_balance": 0.0,
            "balance_currency": "-",
            "position_count": 0,
            "open_order_count": 0,
            "position_notional": 0.0,
            "open_order_notional": 0.0,
            "total_notional": 0.0,
            "market_position_count": 0,
            "market_open_order_count": 0,
            "market_position_notional": 0.0,
            "market_open_order_notional": 0.0,
            "market_notional": 0.0,
            "max_notional_per_market": None,
            "max_total_notional": None,
            "market_limit_usage": None,
            "total_limit_usage": None,
            "exposure_limit_status": "missing_snapshot",
            "exposure_limit_message": "No read-only position snapshot is available yet.",
        }

    balance = snapshot.get("balance") if isinstance(snapshot.get("balance"), dict) else {}
    positions = [item for item in snapshot.get("positions") or [] if isinstance(item, dict)]
    open_orders = [item for item in snapshot.get("open_orders") or [] if isinstance(item, dict)]
    market_id = str(selected_market_id or "")
    market_positions = [item for item in positions if str(item.get("market_id") or "") == market_id]
    market_orders = [item for item in open_orders if str(item.get("market_id") or "") == market_id]
    market_position_notional = sum(_position_notional(item) for item in market_positions)
    market_open_order_notional = sum(_open_order_notional(item) for item in market_orders)
    position_notional = _to_float(snapshot.get("position_notional"))
    if position_notional is None:
        position_notional = sum(_position_notional(item) for item in positions)
    open_order_notional = _to_float(snapshot.get("open_order_notional"))
    if open_order_notional is None:
        open_order_notional = sum(_open_order_notional(item) for item in open_orders)
    total_notional = _to_float(snapshot.get("total_notional"))
    if total_notional is None:
        total_notional = position_notional + open_order_notional

    exposure_limits = _extract_exposure_limits(readiness_report)
    market_limit = exposure_limits.get("max_notional_per_market")
    total_limit = exposure_limits.get("max_total_notional")
    market_notional = market_position_notional + market_open_order_notional
    limit_context = _build_limit_context(
        market_notional=market_notional,
        total_notional=total_notional,
        market_limit=market_limit,
        total_limit=total_limit,
    )

    return {
        "available": True,
        "manual_order_only": bool(balance.get("manual_order_only", True)),
        "snapshot_updated_at": snapshot.get("updated_at") or "-",
        "source": snapshot.get("source") or "-",
        "account_id": snapshot.get("account_id") or "-",
        "available_balance": _to_float(balance.get("available_balance")) or 0.0,
        "total_balance": _to_float(balance.get("total_balance")) or 0.0,
        "balance_currency": balance.get("currency") or "-",
        "position_count": int(snapshot.get("position_count") or len(positions)),
        "open_order_count": int(snapshot.get("open_order_count") or len(open_orders)),
        "position_notional": position_notional,
        "open_order_notional": open_order_notional,
        "total_notional": total_notional,
        "market_position_count": len(market_positions),
        "market_open_order_count": len(market_orders),
        "market_position_notional": market_position_notional,
        "market_open_order_notional": market_open_order_notional,
        "market_notional": market_notional,
        **limit_context,
    }


def render_read_only_account_panel(
    snapshot: dict | None,
    selected_market_id: str | None,
    readiness_report: dict | None = None,
) -> None:
    render_panel_title(
        "Read-only Account Exposure",
        "Position snapshot is observation-only. It does not enable private-key or autonomous execution.",
    )
    summary = build_read_only_account_summary(snapshot, selected_market_id, readiness_report)
    if not summary["available"]:
        st.info("No read-only position snapshot is available yet.")
        return

    if summary["exposure_limit_status"] == "over_limit":
        st.warning(summary["exposure_limit_message"])
    elif summary["exposure_limit_status"] == "near_limit":
        st.info(summary["exposure_limit_message"])
    elif summary["exposure_limit_status"] == "within_limit":
        st.caption(summary["exposure_limit_message"])
    else:
        st.caption("Exposure limits are not available in the latest readiness report.")

    render_kv_section(
        "Account Snapshot",
        [
            ("Account", summary["account_id"]),
            ("Source", summary["source"]),
            ("Updated At", summary["snapshot_updated_at"]),
            ("Manual Order Only", summary["manual_order_only"]),
            ("Available Balance", _money(summary["available_balance"], summary["balance_currency"])),
            ("Total Balance", _money(summary["total_balance"], summary["balance_currency"])),
            ("Positions", summary["position_count"]),
            ("Open Orders", summary["open_order_count"]),
            ("Position Notional", _money(summary["position_notional"], summary["balance_currency"])),
            ("Open Order Notional", _money(summary["open_order_notional"], summary["balance_currency"])),
            ("Selected Market Exposure", _money(summary["market_notional"], summary["balance_currency"])),
            ("Selected Market Rows", f"{summary['market_position_count']} pos / {summary['market_open_order_count']} orders"),
            ("Market Limit Usage", _percent(summary["market_limit_usage"])),
            ("Total Limit Usage", _percent(summary["total_limit_usage"])),
            ("Market Limit", _money(summary["max_notional_per_market"], summary["balance_currency"])),
            ("Total Limit", _money(summary["max_total_notional"], summary["balance_currency"])),
        ],
        metric_label="Total Exposure",
        metric_value=_money(summary["total_notional"], summary["balance_currency"]),
    )


def _position_notional(position: dict[str, Any]) -> float:
    explicit = _to_float(position.get("notional"))
    if explicit is not None:
        return abs(explicit)
    size = _to_float(position.get("size"))
    price = _to_float(position.get("current_price")) or _to_float(position.get("avg_price")) or _to_float(position.get("price"))
    if size is None or price is None:
        return 0.0
    return abs(size * price)


def _open_order_notional(order: dict[str, Any]) -> float:
    explicit = _to_float(order.get("notional"))
    if explicit is not None:
        return abs(explicit)
    size = _to_float(order.get("remaining_size")) or _to_float(order.get("remainingSize")) or _to_float(order.get("size"))
    price = _to_float(order.get("price")) or _to_float(order.get("limit_price")) or _to_float(order.get("limitPrice"))
    if size is None or price is None:
        return 0.0
    return abs(size * price)


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _money(value: Any, currency: Any) -> str:
    numeric = _to_float(value)
    if numeric is None:
        return "-"
    suffix = str(currency or "").strip()
    return f"{numeric:.2f} {suffix}".strip()


def _percent(value: Any) -> str:
    numeric = _to_float(value)
    if numeric is None:
        return "-"
    return f"{numeric * 100:.1f}%"


def _extract_exposure_limits(readiness_report: dict | None) -> dict[str, float | None]:
    checks = readiness_report.get("checks") if isinstance(readiness_report, dict) else []
    if not isinstance(checks, list):
        checks = []
    for check in checks:
        if not isinstance(check, dict):
            continue
        if check.get("name") != "exposure_limits":
            continue
        details = check.get("details") if isinstance(check.get("details"), dict) else {}
        return {
            "max_notional_per_market": _to_float(details.get("max_notional_per_market")),
            "max_total_notional": _to_float(details.get("max_total_notional")),
        }
    return {
        "max_notional_per_market": None,
        "max_total_notional": None,
    }


def _build_limit_context(
    *,
    market_notional: float,
    total_notional: float,
    market_limit: float | None,
    total_limit: float | None,
) -> dict:
    market_usage = _safe_usage(market_notional, market_limit)
    total_usage = _safe_usage(total_notional, total_limit)
    usages = [usage for usage in [market_usage, total_usage] if usage is not None]
    if not usages:
        return {
            "max_notional_per_market": market_limit,
            "max_total_notional": total_limit,
            "market_limit_usage": market_usage,
            "total_limit_usage": total_usage,
            "exposure_limit_status": "missing_limits",
            "exposure_limit_message": "Exposure limits are not available in the latest readiness report.",
        }

    max_usage = max(usages)
    if max_usage > 1.0:
        status = "over_limit"
        message = "Read-only exposure is above configured readiness limits. Manual advisory should stay blocked for added exposure."
    elif max_usage >= 0.8:
        status = "near_limit"
        message = "Read-only exposure is near configured readiness limits. Review before adding manual exposure."
    else:
        status = "within_limit"
        message = "Read-only exposure is within configured readiness limits."

    return {
        "max_notional_per_market": market_limit,
        "max_total_notional": total_limit,
        "market_limit_usage": market_usage,
        "total_limit_usage": total_usage,
        "exposure_limit_status": status,
        "exposure_limit_message": message,
    }


def _safe_usage(notional: float, limit: float | None) -> float | None:
    if limit is None or limit <= 0:
        return None
    return notional / limit
