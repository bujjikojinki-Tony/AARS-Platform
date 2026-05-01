from __future__ import annotations

from datetime import UTC
from datetime import datetime
from uuid import uuid4

from weather_comparison_engine.polymarket_bot.command_parser import parse_command
from weather_comparison_engine.polymarket_bot.models import AuditLog
from weather_comparison_engine.polymarket_bot.models import ExecutionDecision


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _make_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


class CommandRoutes:
    def __init__(self, repositories, opportunity_routes, simulator, settings_routes) -> None:
        self.repositories = repositories
        self.opportunity_routes = opportunity_routes
        self.simulator = simulator
        self.settings_routes = settings_routes

    def post_command(self, command_text: str) -> dict:
        try:
            parsed = parse_command(command_text)
        except ValueError as exc:
            return {"ok": False, "error": str(exc)}

        if parsed.command == "run_scan":
            result = self.opportunity_routes.post_scan()
        elif parsed.command == "show_rules":
            result = self.settings_routes.get_rules()
        elif parsed.command == "set_mode":
            result = self.settings_routes.post_mode(parsed.args[0])
        elif parsed.command == "simulate":
            result = self._handle_simulate(parsed.args[0])
        else:
            result = {"ok": False, "error": "unsupported command"}

        self.repositories.audit_logs.save(
            AuditLog(
                event_id=_make_id("audit"),
                event_type="COMMAND_EXECUTED",
                object_type="Command",
                object_id=parsed.command,
                payload_json=str({"raw": command_text, "ok": result.get("ok", False)}),
                created_at=_now_iso(),
            )
        )
        return result

    def _handle_simulate(self, candidate_id: str) -> dict:
        candidate = self.repositories.opportunity_candidates.get_by_id(candidate_id)
        if candidate is None:
            return {"ok": False, "error": "candidate not found"}

        action = "BUY_YES" if candidate.side == "YES" else "BUY_NO"
        position_size = 25.0
        expected_cost = round(candidate.market_probability * position_size, 4)
        decision = ExecutionDecision(
            decision_id=_make_id("dec"),
            candidate_id=candidate.candidate_id,
            mode="SIMULATION",
            action=action,
            requested_by="local_command",
            approved_by=None,
            approval_required=False,
            approval_status="NOT_REQUIRED",
            position_size=position_size,
            expected_cost=expected_cost,
            risk_status=candidate.risk_status,
            execution_status="QUEUED",
            created_at=_now_iso(),
            executed_at=None,
        )
        self.repositories.execution_decisions.save(decision)
        result = self.simulator.simulate(decision, candidate)
        return {
            "ok": True,
            "decision": decision.to_record(),
            "simulation": result.to_record(),
        }
