from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from weather_telegram_console.settings import (
    get_comparison_history_path,
    get_gate_stack_api_path,
    get_latest_dashboard_rows_path,
    get_manual_advisory_audit_path,
    get_operator_market_context_path,
    get_unified_status_path,
)
from weather_telegram_console.integrations.gate_stack_consumer import consume_gate_stack_payload
from weather_telegram_console.operator_messages import (
    NO_COMPARISON_HISTORY,
    NO_COMPARISON_HISTORY_FOR_SELECTED_MARKET,
    NO_CURRENT_MARKET,
    NO_LATEST_MARKET_SUMMARY,
    SELECTED_MARKET_NOT_IN_SUMMARY,
)


class MarketAPI:
    def load_market_summary(self, market_id: str | None = None) -> dict:
        rows = self._load_json(get_latest_dashboard_rows_path())
        if not isinstance(rows, list) or not rows:
            raise FileNotFoundError(NO_LATEST_MARKET_SUMMARY)

        target_market_id = (market_id or self._get_current_market_id() or "").strip()
        if target_market_id:
            for row in rows:
                if isinstance(row, dict) and str(row.get("market_id") or "") == target_market_id:
                    return self._build_market_summary(row)
            raise FileNotFoundError(f"{SELECTED_MARKET_NOT_IN_SUMMARY} market_id=`{target_market_id}`")

        for row in rows:
            if isinstance(row, dict):
                return self._build_market_summary(row)

        raise FileNotFoundError(NO_LATEST_MARKET_SUMMARY)

    def load_market_timeline(self, market_id: str | None = None, limit: int = 8) -> list[dict]:
        history = self._load_json(get_comparison_history_path())
        if not isinstance(history, list) or not history:
            raise FileNotFoundError(NO_COMPARISON_HISTORY)

        target_market_id = (market_id or self._get_current_market_id() or "").strip()
        if not target_market_id:
            raise FileNotFoundError(NO_CURRENT_MARKET)

        filtered = [
            row
            for row in history
            if isinstance(row, dict) and str(row.get("market_id") or "") == target_market_id
        ]
        if not filtered:
            raise FileNotFoundError(
                f"{NO_COMPARISON_HISTORY_FOR_SELECTED_MARKET} market_id=`{target_market_id}`"
            )

        filtered.sort(key=lambda row: str(row.get("timestamp") or ""), reverse=True)
        return filtered[:limit]

    def _build_market_summary(self, row: dict) -> dict:
        market_id = str(row.get("market_id") or "").strip()
        advisory_events = self._load_manual_advisory_events(market_id)
        gate_stack_api = self._load_json(get_gate_stack_api_path())
        unified_status = self._load_json(get_unified_status_path())
        compact_gate_stack = self._build_compact_gate_stack(
            row,
            gate_stack_api=gate_stack_api,
            unified_status=unified_status,
        )
        data_availability = {
            "market_snapshot_ref_present": bool(row.get("market_snapshot_ref")),
            "forecast_snapshot_ref_present": bool(row.get("forecast_snapshot_ref")),
            "manual_advisory_events_present": bool(advisory_events),
            "manual_advisory_audit_available": get_manual_advisory_audit_path().exists(),
        }
        return {
            **row,
            "compact_gate_stack": compact_gate_stack,
            "promotion_state": compact_gate_stack.get("promotion_state") or _extract_promotion_state(
                gate_stack_api,
                unified_status,
                row,
            ),
            "advisory_summary": self._build_advisory_summary(advisory_events),
            "data_availability": data_availability,
        }

    def _build_compact_gate_stack(
        self,
        row: dict,
        *,
        gate_stack_api: dict | None = None,
        unified_status: dict | None = None,
    ) -> dict:
        market_id = str(row.get("market_id") or "").strip()
        if isinstance(gate_stack_api, dict) and str(gate_stack_api.get("schema_version") or "") == "gate_stack_api.v1":
            consumer = consume_gate_stack_payload(gate_stack_api, market_id=market_id)
            source_payload = consumer.market_view if isinstance(getattr(consumer, "market_view", None), dict) else consumer.payload
            gate_stack = source_payload.get("gate_stack") if isinstance(source_payload.get("gate_stack"), dict) else source_payload
            if isinstance(gate_stack, dict):
                promotion_state = _extract_promotion_state(source_payload, gate_stack_api, unified_status, row)
                return {
                    "resolver_gate": str(gate_stack.get("resolver_gate") or "pass"),
                    "resolver_gate_reasons": [
                        str(item) for item in gate_stack.get("resolver_gate_reasons") or []
                    ],
                    "probability_gate": str(gate_stack.get("probability_gate") or "-"),
                    "freshness_gate": str(gate_stack.get("freshness_gate") or "-"),
                    "authorization_gate": str(gate_stack.get("authorization_gate") or "-"),
                    "execution_gate": str(gate_stack.get("execution_gate") or "-"),
                    "block_reasons": [str(item) for item in gate_stack.get("block_reasons") or []],
                    "severity": str(source_payload.get("severity") or gate_stack_api.get("severity") or "medium"),
                    "recommended_operator_action": str(
                        source_payload.get("recommended_operator_action")
                        or gate_stack_api.get("recommended_operator_action")
                        or "hold_execution_and_review"
                    ),
                    "source": consumer.gate_source,
                    "promotion_state": promotion_state,
                    "promotion_reason": promotion_state.get("promotion_reason"),
                    "demotion_reason": promotion_state.get("demotion_reason"),
                }

        if isinstance(unified_status, dict):
            current_market = unified_status.get("current_market") or {}
            current_market_id = str(current_market.get("market_id") or "").strip()
            gate_stack = unified_status.get("gate_stack")
            if market_id and market_id == current_market_id and isinstance(gate_stack, dict):
                promotion_state = _extract_promotion_state(unified_status, row)
                return {
                    "resolver_gate": str(gate_stack.get("resolver_gate") or "pass"),
                    "resolver_gate_reasons": [
                        str(item) for item in gate_stack.get("resolver_gate_reasons") or []
                    ],
                    "probability_gate": str(gate_stack.get("probability_gate") or "-"),
                    "freshness_gate": str(gate_stack.get("freshness_gate") or "-"),
                    "authorization_gate": str(gate_stack.get("authorization_gate") or "-"),
                    "execution_gate": str(gate_stack.get("execution_gate") or "-"),
                    "block_reasons": [str(item) for item in gate_stack.get("block_reasons") or []],
                    "source": "unified_fallback",
                    "promotion_state": promotion_state,
                    "promotion_reason": promotion_state.get("promotion_reason"),
                    "demotion_reason": promotion_state.get("demotion_reason"),
                }

        resolver_status = str(row.get("resolver_status") or row.get("rule_status") or "")
        resolver_confidence = float(row.get("resolver_confidence") or 0.0)
        source_match_grade = str(row.get("source_match_grade") or "")
        reasons: list[str] = []
        if resolver_status.strip().lower() != "matched":
            reasons.append("resolver_not_matched")
        if resolver_confidence < 0.7:
            reasons.append("resolver_confidence_low")
        if source_match_grade.strip().lower() in {"", "unmatched", "family_only"}:
            reasons.append("resolver_source_not_exact")
        return {
            "resolver_gate": "blocked" if reasons else "pass",
            "authorization_gate": "blocked" if reasons else "pass",
            "resolver_gate_reasons": reasons,
            "source": "local_fallback",
            "promotion_state": _extract_promotion_state(row),
            "promotion_reason": _extract_promotion_state(row).get("promotion_reason"),
            "demotion_reason": _extract_promotion_state(row).get("demotion_reason"),
        }

    def _get_current_market_id(self) -> str | None:
        operator_context = self._load_json(get_operator_market_context_path())
        if isinstance(operator_context, dict):
            market_id = str(operator_context.get("market_id") or "").strip()
            if market_id:
                return market_id

        report = self._load_json(get_unified_status_path())
        if not isinstance(report, dict):
            return None
        current_market = report.get("current_market") or {}
        return str(current_market.get("market_id") or "").strip() or None

    def _load_manual_advisory_events(self, market_id: str) -> list[dict]:
        path = get_manual_advisory_audit_path()
        if not market_id or not path.exists():
            return []

        events: list[dict] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except Exception:
                continue
            if not isinstance(payload, dict):
                continue
            if str(payload.get("market_id") or "") != market_id:
                continue
            events.append(payload)
        events.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
        return events

    def _build_advisory_summary(self, events: list[dict]) -> dict:
        latest = events[0] if events else {}
        payload = latest.get("payload") or {}
        manual_trade_ticket = payload.get("manual_trade_ticket") or {}
        return {
            "event_count": len(events),
            "latest_event_type": latest.get("event_type"),
            "latest_created_at": latest.get("created_at"),
            "latest_decision": payload.get("decision") or payload.get("approval_status"),
            "latest_gate_status": payload.get("gate_status"),
            "latest_price": manual_trade_ticket.get("price"),
            "latest_size": manual_trade_ticket.get("size"),
        }

    def _load_json(self, path: Path) -> Any:
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None


def _extract_promotion_state(*payloads: dict | None) -> dict:
    for payload in payloads:
        if not isinstance(payload, dict):
            continue
        candidate = payload.get("promotion_state")
        if isinstance(candidate, dict):
            return candidate
        probability = payload.get("probability")
        if isinstance(probability, dict):
            candidate = probability.get("promotion_state")
            if isinstance(candidate, dict):
                return candidate
        validation = payload.get("validation")
        if isinstance(validation, dict):
            candidate = validation.get("promotion_state")
            if isinstance(candidate, dict):
                return candidate
    return {}
