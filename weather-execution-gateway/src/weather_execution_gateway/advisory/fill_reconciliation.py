from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class HumanFillReconciler:
    def __init__(
        self,
        *,
        fills_path: str | Path,
        position_snapshot_path: str | Path,
        intent_preview_path: str | Path | None = None,
        price_tolerance_pct: float = 0.03,
        notional_tolerance_pct: float = 0.05,
    ) -> None:
        self.fills_path = Path(fills_path)
        self.position_snapshot_path = Path(position_snapshot_path)
        self.intent_preview_path = Path(intent_preview_path) if intent_preview_path else None
        self.price_tolerance_pct = price_tolerance_pct
        self.notional_tolerance_pct = notional_tolerance_pct

    def build_report(self) -> dict:
        fills = _load_jsonl(self.fills_path)
        position_snapshot = _load_json(self.position_snapshot_path, default={})
        intent_preview = (
            _load_json(self.intent_preview_path, default={})
            if self.intent_preview_path is not None
            else {}
        )
        positions = [
            position
            for position in position_snapshot.get("positions", [])
            if isinstance(position, dict)
        ]
        open_orders = [
            order
            for order in position_snapshot.get("open_orders", [])
            if isinstance(order, dict)
        ]

        items = [
            self._reconcile_fill(
                fill=fill,
                positions=positions,
                open_orders=open_orders,
                intent_preview=intent_preview,
            )
            for fill in fills
            if isinstance(fill, dict)
        ]
        status_counts = _count_by(items, "reconciliation_status")

        return {
            "schema_version": "human_fill_reconciliation_report.v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "fills_path": str(self.fills_path),
            "position_snapshot_path": str(self.position_snapshot_path),
            "intent_preview_path": str(self.intent_preview_path) if self.intent_preview_path else None,
            "position_snapshot_updated_at": position_snapshot.get("updated_at"),
            "fill_count": len(items),
            "reconciled_count": status_counts.get("reconciled", 0),
            "needs_review_count": status_counts.get("needs_review", 0),
            "unmatched_count": status_counts.get("unmatched", 0),
            "manual_order_only": True,
            "autonomous_execution_allowed": False,
            "overall_status": _overall_status(status_counts),
            "items": items,
        }

    def write_report(self, path: str | Path) -> Path:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps(self.build_report(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return out

    def _reconcile_fill(
        self,
        *,
        fill: dict,
        positions: list[dict],
        open_orders: list[dict],
        intent_preview: dict,
    ) -> dict:
        market_id = str(fill.get("market_id") or "")
        side = str(fill.get("side") or "").lower()
        fill_price = _to_float(fill.get("price"))
        fill_size = _to_float(fill.get("size"))
        fill_notional = _to_float(fill.get("notional"))
        if fill_notional is None and fill_price is not None and fill_size is not None:
            fill_notional = abs(fill_price * fill_size)

        matching_positions = _matching_market_rows(positions, market_id)
        matching_open_orders = _matching_market_rows(open_orders, market_id)
        position_notional = sum(_row_notional(position) for position in matching_positions)
        open_order_notional = sum(_row_notional(order) for order in matching_open_orders)
        expected_price = self._expected_price(fill=fill, intent_preview=intent_preview)
        price_delta = (
            abs(fill_price - expected_price)
            if fill_price is not None and expected_price is not None
            else None
        )
        price_delta_pct = (
            price_delta / expected_price
            if price_delta is not None and expected_price not in {None, 0}
            else None
        )
        notional_covered = (
            position_notional + open_order_notional
        )
        notional_delta = (
            max((fill_notional or 0.0) - notional_covered, 0.0)
            if fill_notional is not None
            else None
        )
        notional_delta_pct = (
            notional_delta / fill_notional
            if notional_delta is not None and fill_notional not in {None, 0}
            else None
        )
        checks = {
            "market_seen_in_position_snapshot": bool(matching_positions or matching_open_orders),
            "position_or_order_covers_fill": (
                notional_delta_pct is not None
                and notional_delta_pct <= self.notional_tolerance_pct
            ),
            "price_within_tolerance": (
                price_delta_pct is None
                or price_delta_pct <= self.price_tolerance_pct
            ),
        }
        status = _status_from_checks(checks)

        return {
            "fill_id": fill.get("fill_id"),
            "intent_id": fill.get("intent_id"),
            "signal_id": fill.get("signal_id"),
            "market_id": market_id,
            "side": side,
            "price": fill_price,
            "size": fill_size,
            "notional": fill_notional,
            "expected_price": expected_price,
            "price_delta": price_delta,
            "price_delta_pct": price_delta_pct,
            "position_notional": position_notional,
            "open_order_notional": open_order_notional,
            "covered_notional": notional_covered,
            "notional_delta": notional_delta,
            "notional_delta_pct": notional_delta_pct,
            "matching_position_count": len(matching_positions),
            "matching_open_order_count": len(matching_open_orders),
            "checks": checks,
            "reconciliation_status": status,
            "review_reason": _review_reason(checks),
            "manual_order_only": True,
        }

    def _expected_price(self, *, fill: dict, intent_preview: dict) -> float | None:
        if str(intent_preview.get("intent_id") or "") == str(fill.get("intent_id") or ""):
            return _to_float(intent_preview.get("price"))
        return None


def _load_json(path: Path | None, *, default: Any) -> Any:
    if path is None or not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def _matching_market_rows(rows: list[dict], market_id: str) -> list[dict]:
    return [row for row in rows if str(row.get("market_id") or "") == market_id]


def _row_notional(row: dict) -> float:
    explicit = _to_float(row.get("notional"))
    if explicit is not None:
        return abs(explicit)
    price = _to_float(row.get("current_price")) or _to_float(row.get("price"))
    size = _to_float(row.get("size")) or _to_float(row.get("remaining_size"))
    if price is None or size is None:
        return 0.0
    return abs(price * size)


def _status_from_checks(checks: dict[str, bool]) -> str:
    if not checks["market_seen_in_position_snapshot"]:
        return "unmatched"
    if all(checks.values()):
        return "reconciled"
    return "needs_review"


def _review_reason(checks: dict[str, bool]) -> str | None:
    if not checks["market_seen_in_position_snapshot"]:
        return "fill_market_not_seen_in_position_snapshot"
    if not checks["position_or_order_covers_fill"]:
        return "position_snapshot_does_not_cover_fill_notional"
    if not checks["price_within_tolerance"]:
        return "fill_price_outside_expected_tolerance"
    return None


def _overall_status(status_counts: dict[str, int]) -> str:
    if not status_counts:
        return "no_fills"
    if status_counts.get("unmatched", 0) or status_counts.get("needs_review", 0):
        return "needs_review"
    return "reconciled"


def _count_by(items: list[dict], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        value = str(item.get(key) or "unknown")
        counts[value] = counts.get(value, 0) + 1
    return counts


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
