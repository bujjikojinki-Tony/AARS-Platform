from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class PositionExposureReader:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> dict:
        if not self.path.exists():
            return {
                "schema_version": "position_snapshot.v1",
                "updated_at": None,
                "balance": {},
                "positions": [],
                "open_orders": [],
                "snapshot_available": False,
                "source_path": str(self.path),
            }

        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            payload = {"positions": payload}
        if not isinstance(payload, dict):
            payload = {"positions": []}

        payload.setdefault("positions", [])
        payload.setdefault("open_orders", [])
        payload.setdefault("balance", {})
        payload["snapshot_available"] = True
        payload["source_path"] = str(self.path)
        return payload

    def exposure_for_market(self, market_id: str) -> dict:
        snapshot = self.load()
        balance = snapshot.get("balance") if isinstance(snapshot.get("balance"), dict) else {}
        positions = snapshot.get("positions") or []
        open_orders = snapshot.get("open_orders") or []

        market_notional = 0.0
        total_notional = 0.0
        market_position_notional = 0.0
        market_open_order_notional = 0.0
        total_position_notional = 0.0
        total_open_order_notional = 0.0
        market_position_count = 0
        market_open_order_count = 0

        for position in positions:
            if not isinstance(position, dict):
                continue

            notional = _position_notional(position)
            total_position_notional += notional

            if str(position.get("market_id")) == str(market_id):
                market_position_notional += notional
                market_position_count += 1

        for order in open_orders:
            if not isinstance(order, dict):
                continue

            notional = _open_order_notional(order)
            total_open_order_notional += notional

            if str(order.get("market_id")) == str(market_id):
                market_open_order_notional += notional
                market_open_order_count += 1

        market_notional = market_position_notional + market_open_order_notional
        total_notional = total_position_notional + total_open_order_notional

        return {
            "schema_version": "position_exposure.v1",
            "computed_at": datetime.now(timezone.utc).isoformat(),
            "snapshot_updated_at": snapshot.get("updated_at"),
            "snapshot_available": bool(snapshot.get("snapshot_available", False)),
            "market_id": market_id,
            "market_notional": market_notional,
            "total_notional": total_notional,
            "market_position_notional": market_position_notional,
            "market_open_order_notional": market_open_order_notional,
            "total_position_notional": total_position_notional,
            "total_open_order_notional": total_open_order_notional,
            "market_position_count": market_position_count,
            "market_open_order_count": market_open_order_count,
            "total_position_count": len([p for p in positions if isinstance(p, dict)]),
            "total_open_order_count": len([o for o in open_orders if isinstance(o, dict)]),
            "available_balance": _to_float(balance.get("available_balance")),
            "total_balance": _to_float(balance.get("total_balance")),
            "balance_currency": balance.get("currency"),
            "manual_order_only": bool(balance.get("manual_order_only", True)),
            "balance_snapshot_available": bool(balance.get("snapshot_available", False)),
            "source_path": snapshot.get("source_path"),
        }


def _position_notional(position: dict[str, Any]) -> float:
    explicit_notional = _to_float(position.get("notional"))
    if explicit_notional is not None:
        return abs(explicit_notional)

    size = _to_float(position.get("size"))
    price = (
        _to_float(position.get("current_price"))
        or _to_float(position.get("avg_price"))
        or _to_float(position.get("price"))
    )
    if size is None or price is None:
        return 0.0

    return abs(size * price)


def _open_order_notional(order: dict[str, Any]) -> float:
    explicit_notional = _to_float(order.get("notional"))
    if explicit_notional is not None:
        return abs(explicit_notional)

    size = (
        _to_float(order.get("remaining_size"))
        or _to_float(order.get("remainingSize"))
        or _to_float(order.get("size"))
    )
    price = (
        _to_float(order.get("price"))
        or _to_float(order.get("limit_price"))
        or _to_float(order.get("limitPrice"))
    )
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
