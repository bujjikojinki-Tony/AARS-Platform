from __future__ import annotations

from fastapi import APIRouter

from backend.api.command_parser import parse_command
from backend.models.core import AuditLogEvent
from backend.models.enums import ActionStatus


def create_command_router(repository, strategy_runner, simulator, rule_registry) -> APIRouter:
    router = APIRouter(prefix="/api/command", tags=["command"])

    @router.post("")
    def run_command(payload: dict):
        from uuid import uuid4

        command = payload.get("command", "")
        intent = parse_command(command)
        try:
            if intent.type == "RUN_SCAN":
                candidates = strategy_runner.run_once()
                result = {"status": "ok", "candidates_count": len(candidates)}
            elif intent.type == "LIST_OPPORTUNITIES":
                result = {"status": "ok", "items": repository.list_opportunity_candidates()}
            elif intent.type == "SIMULATE":
                sim = simulator.simulate(intent.candidate_id)
                result = {"status": "ok", "simulation": sim.model_dump()}
            elif intent.type == "BLOCK":
                repository.update_candidate_action_status(intent.candidate_id, ActionStatus.BLOCKED)
                result = {"status": "ok", "candidate_id": intent.candidate_id, "action_status": "BLOCKED"}
            elif intent.type == "SET_MODE":
                mode = rule_registry.set_mode(intent.mode)
                result = {"status": "ok", "mode": mode}
            elif intent.type == "SHOW_RULES":
                result = {"status": "ok", "rules": rule_registry.get_rules()}
            elif intent.type == "SHOW_HISTORY":
                result = {"status": "ok", "audit": repository.list_table("audit_logs")}
            else:
                result = {"status": "error", "code": intent.type, "message": "unsupported or invalid command"}
            repository.save_audit_log(
                AuditLogEvent(
                    event_id=f"evt_{uuid4().hex[:10]}",
                    event_type="COMMAND_EXECUTED" if result["status"] == "ok" else "COMMAND_REJECTED",
                    object_type="Command",
                    object_id=f"cmd_{uuid4().hex[:10]}",
                    payload={"command": command, "result": result},
                )
            )
            return result
        except Exception as exc:
            repository.save_audit_log(
                AuditLogEvent(
                    event_id=f"evt_{uuid4().hex[:10]}",
                    event_type="COMMAND_REJECTED",
                    object_type="Command",
                    object_id=f"cmd_{uuid4().hex[:10]}",
                    payload={"command": command, "error": str(exc)},
                )
            )
            return {"status": "error", "message": str(exc)}

    return router
