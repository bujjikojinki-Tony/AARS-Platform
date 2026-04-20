import json
from typing import Any, Dict, List

from openai import OpenAI

from config import OPENAI_API_KEY, OPENAI_REVIEW_MODEL


class RealReviewService:
    def __init__(self) -> None:
        self.enabled = bool(OPENAI_API_KEY)
        self.client = OpenAI(api_key=OPENAI_API_KEY) if self.enabled else None
        self.model = OPENAI_REVIEW_MODEL

    def _build_payload(self, session) -> Dict[str, Any]:
        return {
            "project_id": session.project_id,
            "project_name": session.name,
            "current_step": session.current_step,
            "health": session.health,
            "status": session.status,
            "agents": session.agents,
            "tasks": [
                {
                    "task_id": t.task_id,
                    "name": t.name,
                    "agent_type": t.agent_type,
                    "status": t.status,
                    "result": t.result,
                    "created_at": t.created_at,
                }
                for t in session.tasks
            ],
            "latest_stable_view": (
                {
                    "stable_step": session.latest_stable_view.stable_step,
                    "accepted_outputs": session.latest_stable_view.accepted_outputs,
                    "open_risks": session.latest_stable_view.open_risks,
                    "reentry_point": session.latest_stable_view.reentry_point,
                    "supervisor_note": session.latest_stable_view.supervisor_note,
                }
                if session.latest_stable_view
                else None
            ),
            "risk_objects": [
                {
                    "risk_id": r.risk_id,
                    "title": r.title,
                    "description": r.description,
                    "severity": r.severity,
                    "mitigation": r.mitigation,
                    "status": r.status,
                }
                for r in session.risk_objects
            ],
            "health_snapshot": (
                {
                    "overall_health": session.health_snapshot.overall_health,
                    "session_status": session.health_snapshot.session_status,
                    "current_step": session.health_snapshot.current_step,
                    "total_tasks": session.health_snapshot.total_tasks,
                    "completed_tasks": session.health_snapshot.completed_tasks,
                    "blocked_tasks": session.health_snapshot.blocked_tasks,
                    "failed_tasks": session.health_snapshot.failed_tasks,
                    "generated_at": session.health_snapshot.generated_at,
                }
                if session.health_snapshot
                else None
            ),
            "recovery_path": (
                {
                    "current_step": session.recovery_path.current_step,
                    "latest_stable_step": session.recovery_path.latest_stable_step,
                    "reentry_point": session.recovery_path.reentry_point,
                    "suggested_action": session.recovery_path.suggested_action,
                    "recovery_mode": session.recovery_path.recovery_mode,
                    "generated_at": session.recovery_path.generated_at,
                }
                if session.recovery_path
                else None
            ),
            "gate_logs_tail": [
                {
                    "gate_name": g.gate_name,
                    "allowed": g.allowed,
                    "reason": g.reason,
                    "blocking_risks": g.blocking_risks,
                    "action_name": g.action_name,
                    "generated_at": g.generated_at,
                }
                for g in session.gate_logs[-8:]
            ],
        }

    def review_session(self, session) -> str:
        if not self.enabled:
            return (
                "Review Result: FALLBACK MODE\n"
                "OPENAI_API_KEY 未配置，仍在使用本地 fallback review。\n"
                "建议：配置 OPENAI_API_KEY 后再启用 real review。"
            )

        payload = self._build_payload(session)

        instructions = (
            "You are an AARS governance reviewer.\n"
            "Evaluate the project session as a governed runtime, not as a general chatbot.\n"
            "Focus on:\n"
            "1. admissibility of progression\n"
            "2. governance health\n"
            "3. open risks\n"
            "4. whether a stable checkpoint is sufficient\n"
            "5. recommended next action\n\n"
            "Return concise plain text in this exact structure:\n"
            "Review Result: <PASS | PASS WITH NOTES | BLOCKED>\n"
            "Admissibility: <one sentence>\n"
            "Health Assessment: <one sentence>\n"
            "Open Risks:\n"
            "- ...\n"
            "- ...\n"
            "Stable View Judgment: <one sentence>\n"
            "Recommended Next Action: <one sentence>\n"
        )

        response = self.client.responses.create(
            model=self.model,
            instructions=instructions,
            input=json.dumps(payload, ensure_ascii=False),
        )

        return response.output_text.strip()


review_service = RealReviewService()
