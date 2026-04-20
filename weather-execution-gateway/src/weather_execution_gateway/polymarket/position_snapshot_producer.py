from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from weather_execution_gateway.polymarket.user_activity import PolymarketUserActivityReader


class PositionSnapshotProducer:
    def __init__(self, reader: PolymarketUserActivityReader) -> None:
        self.reader = reader

    def build_snapshot(self) -> dict:
        payload = self.reader.get_positions()
        raw_positions = payload.get("positions") or []
        raw_open_orders = payload.get("open_orders") or payload.get("orders") or []
        balance = normalize_balance(payload.get("balance") or payload)
        positions = [
            normalize_position(position)
            for position in raw_positions
            if isinstance(position, dict)
        ]
        open_orders = [
            normalize_open_order(order)
            for order in raw_open_orders
            if isinstance(order, dict)
        ]
        position_notional = sum(float(position.get("notional") or 0.0) for position in positions)
        open_order_notional = sum(float(order.get("notional") or 0.0) for order in open_orders)

        return {
            "schema_version": "position_snapshot.v1",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "source": payload.get("source", "unknown"),
            "source_path": payload.get("source_path"),
            "account_id": payload.get("account_id") or payload.get("funder"),
            "balance": balance,
            "positions": positions,
            "open_orders": open_orders,
            "position_count": len(positions),
            "open_order_count": len(open_orders),
            "position_notional": position_notional,
            "open_order_notional": open_order_notional,
            "total_notional": position_notional + open_order_notional,
        }

    def write_snapshot(self, path: str | Path) -> Path:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        snapshot = self.build_snapshot()
        out.write_text(
            json.dumps(snapshot, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return out


def normalize_position(position: dict[str, Any]) -> dict:
    market_id = _first_value(position, ["market_id", "marketId", "condition_id", "conditionId"])
    token_id = _first_value(position, ["token_id", "tokenId", "asset_id", "assetId"])
    outcome = _first_value(position, ["outcome", "side", "asset_outcome"])
    size = _to_float(_first_value(position, ["size", "balance", "shares", "quantity"]))
    current_price = _to_float(_first_value(position, ["current_price", "currentPrice", "price"]))
    avg_price = _to_float(_first_value(position, ["avg_price", "avgPrice", "average_price"]))
    notional = _to_float(position.get("notional"))

    price_for_notional = current_price if current_price is not None else avg_price
    if notional is None and size is not None and price_for_notional is not None:
        notional = abs(size * price_for_notional)

    return {
        "market_id": str(market_id) if market_id is not None else None,
        "token_id": str(token_id) if token_id is not None else None,
        "outcome": str(outcome).lower() if outcome is not None else None,
        "size": size,
        "current_price": current_price,
        "avg_price": avg_price,
        "notional": abs(notional) if notional is not None else 0.0,
        "raw_ref": {
            "title": _first_value(position, ["title", "market_title", "marketTitle"]),
            "slug": _first_value(position, ["slug", "market_slug", "marketSlug"]),
        },
    }


def normalize_open_order(order: dict[str, Any]) -> dict:
    market_id = _first_value(order, ["market_id", "marketId", "condition_id", "conditionId"])
    token_id = _first_value(order, ["token_id", "tokenId", "asset_id", "assetId"])
    outcome = _first_value(order, ["outcome", "side", "asset_outcome"])
    order_id = _first_value(order, ["order_id", "orderId", "id"])
    status = _first_value(order, ["status", "state"])
    price = _to_float(_first_value(order, ["price", "limit_price", "limitPrice"]))
    size = _to_float(_first_value(order, ["size", "original_size", "originalSize", "quantity"]))
    remaining_size = _to_float(
        _first_value(order, ["remaining_size", "remainingSize", "remaining", "size_matched_remaining"])
    )
    notional = _to_float(order.get("notional"))

    size_for_notional = remaining_size if remaining_size is not None else size
    if notional is None and size_for_notional is not None and price is not None:
        notional = abs(size_for_notional * price)

    return {
        "order_id": str(order_id) if order_id is not None else None,
        "market_id": str(market_id) if market_id is not None else None,
        "token_id": str(token_id) if token_id is not None else None,
        "outcome": str(outcome).lower() if outcome is not None else None,
        "status": str(status).lower() if status is not None else None,
        "price": price,
        "size": size,
        "remaining_size": remaining_size,
        "notional": abs(notional) if notional is not None else 0.0,
        "raw_ref": {
            "title": _first_value(order, ["title", "market_title", "marketTitle"]),
            "slug": _first_value(order, ["slug", "market_slug", "marketSlug"]),
        },
    }


def normalize_balance(payload: dict[str, Any]) -> dict:
    available = _to_float(
        _first_value(
            payload,
            ["available_balance", "availableBalance", "available", "cash", "collateral"],
        )
    )
    total = _to_float(_first_value(payload, ["total_balance", "totalBalance", "total", "equity"]))
    currency = _first_value(payload, ["currency", "asset", "denomination"]) or "USDC"

    return {
        "available_balance": available,
        "total_balance": total,
        "currency": str(currency),
        "manual_order_only": bool(payload.get("manual_order_only", True)),
        "snapshot_available": available is not None or total is not None,
    }


def _first_value(payload: dict[str, Any], keys: list[str]) -> Any:
    for key in keys:
        value = payload.get(key)
        if value is not None:
            return value
    return None


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
