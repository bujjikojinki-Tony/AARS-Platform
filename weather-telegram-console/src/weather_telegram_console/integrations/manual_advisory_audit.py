from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


def build_operator_ack_event(
    *,
    signal_payload: dict,
    approval: dict,
    operator_user_id: int,
    intent_id: str,
) -> dict:
    return {
        "schema_version": "manual_advisory_event.v1",
        "event_id": f"manual_adv_{uuid4().hex[:10]}",
        "event_type": "operator_acknowledged_manual_advisory",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "execution_mode": "manual_advisory",
        "manual_order_required": True,
        "autonomous_execution_allowed": False,
        "intent_id": intent_id,
        "signal_id": signal_payload.get("signal_id") or approval.get("signal_id"),
        "market_id": signal_payload.get("market_id"),
        "operator_user_id": operator_user_id,
        "payload": {
            "approval_id": approval.get("approval_id"),
            "decision": approval.get("decision"),
            "approval_status": "operator_acknowledged",
            "approval_purpose": "operator_review_not_auto_execution",
            "manual_trade_ticket": signal_payload.get("manual_trade_ticket"),
        },
    }


def append_manual_advisory_event(path: Path, event: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    return path
