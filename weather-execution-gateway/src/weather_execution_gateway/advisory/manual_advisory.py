from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


class ManualAdvisoryAuditStore:
    def __init__(
        self,
        audit_path: str | Path = "data/outputs/manual_advisory_audit.jsonl",
        fills_path: str | Path = "data/outputs/human_fills.jsonl",
    ) -> None:
        self.audit_path = Path(audit_path)
        self.fills_path = Path(fills_path)

    def append_event(self, event: dict) -> Path:
        _append_jsonl(self.audit_path, event)
        return self.audit_path

    def record_human_fill(self, fill: dict) -> tuple[Path, Path]:
        event = build_manual_advisory_event(
            event_type="human_fill_reported",
            intent_id=str(fill.get("intent_id") or ""),
            signal_id=str(fill.get("signal_id") or ""),
            market_id=str(fill.get("market_id") or ""),
            operator_user_id=fill.get("operator_user_id"),
            payload={"fill": fill},
        )
        _append_jsonl(self.fills_path, fill)
        _append_jsonl(self.audit_path, event)
        return self.fills_path, self.audit_path


def build_manual_advisory_event(
    *,
    event_type: str,
    intent_id: str,
    signal_id: str = "",
    market_id: str = "",
    operator_user_id: int | None = None,
    payload: dict[str, Any] | None = None,
) -> dict:
    return {
        "schema_version": "manual_advisory_event.v1",
        "event_id": f"manual_adv_{uuid4().hex[:10]}",
        "event_type": event_type,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "execution_mode": "manual_advisory",
        "manual_order_required": True,
        "autonomous_execution_allowed": False,
        "intent_id": intent_id,
        "signal_id": signal_id,
        "market_id": market_id,
        "operator_user_id": operator_user_id,
        "payload": payload or {},
    }


def build_human_fill_record(
    *,
    intent_id: str,
    market_id: str,
    side: str,
    price: float,
    size: float,
    signal_id: str = "",
    operator_user_id: int = 0,
    notes: str = "",
) -> dict:
    return {
        "schema_version": "human_fill.v1",
        "fill_id": f"human_fill_{uuid4().hex[:10]}",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "execution_mode": "manual_advisory",
        "intent_id": intent_id,
        "signal_id": signal_id,
        "market_id": market_id,
        "side": side,
        "price": float(price),
        "size": float(size),
        "notional": float(price) * float(size),
        "operator_user_id": operator_user_id,
        "notes": notes,
        "source": "human_operator_reported",
    }


def _append_jsonl(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")
