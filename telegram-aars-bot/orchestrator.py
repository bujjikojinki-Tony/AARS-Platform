from datetime import datetime
from uuid import uuid4

from models import (
    ProjectSession,
    AgentTask,
    LatestStableView,
    HealthSnapshot,
    RiskObject,
    RecoveryPath,
    GateDecision,
    GateLog,
)
from rule_registry import rule_registry


class AARSOrchestrator:
    def create_project(self, name: str) -> ProjectSession:
        project_id = f"proj-{uuid4().hex[:8]}"
        session = ProjectSession(
            project_id=project_id,
            name=name,
            current_step="Intent Framing",
            health="healthy",
            status="active",
            agents=0,
        )
        self.refresh_governance(session)
        return session

    def spawn_agents(self, session: ProjectSession, count: int) -> ProjectSession:
        session.agents += count
        session.updated_at = datetime.utcnow().isoformat()
        self.refresh_governance(session)
        return session

    def run_step(self, session: ProjectSession, step_name: str) -> tuple[ProjectSession, GateDecision]:
        self.refresh_governance(session)

        if step_name in ["Task Execution", "Concept Layer Validation"]:
            decision = rule_registry.evaluate_as_gate(
                "deeper_progression",
                "deeper_progression_gate",
                session,
            )
            self._log_gate_decision(session, decision, f"run_step:{step_name}")
            if not decision.allowed:
                return session, decision

        decision = GateDecision(
            gate_name="execution_gate",
            allowed=True,
            reason=f"Step '{step_name}' accepted and completed.",
            blocking_risks=[],
        )
        self._log_gate_decision(session, decision, f"run_step:{step_name}")

        task = AgentTask(
            task_id=f"task-{uuid4().hex[:8]}",
            name=step_name,
            agent_type="builder",
            status="completed",
            result=f"{step_name} completed",
        )
        session.tasks.append(task)
        session.current_step = step_name
        session.updated_at = datetime.utcnow().isoformat()
        self.refresh_governance(session)

        return session, decision

    def review(self, session: ProjectSession) -> str:
        self.refresh_governance(session)

        results = rule_registry.evaluate("review", session)
        failed = [r for r in results if not r.passed]

        high_open_risks = [r for r in session.risk_objects if r.severity == "high" and r.status == "open"]
        has_stable_view = session.latest_stable_view is not None

        if high_open_risks:
            session.health = "degraded"
            risk_lines = "\n".join(f"- {r.risk_id}: {r.title}" for r in high_open_risks)
            result = (
                "Review Result: BLOCKED\n"
                "Admissibility: Deeper progression is not admissible.\n"
                "Health Assessment: High-severity open risks remain.\n"
                f"Open Risks:\n{risk_lines}\n"
                f"Stable View Judgment: {'Stable checkpoint exists but is insufficient for safe continuation.' if has_stable_view else 'No stable checkpoint exists.'}\n"
                "Recommended Next Action: Resolve blocking risks and regenerate governance state."
            )
        elif failed:
            session.health = "warning"
            notes = "\n".join(f"- {r.rule_name}: {r.message}" for r in failed)
            result = (
                "Review Result: PASS WITH NOTES\n"
                "Admissibility: Early or bounded progression only.\n"
                "Health Assessment: Governance baseline checks are not fully satisfied.\n"
                f"Open Risks:\n{notes}\n"
                f"Stable View Judgment: {'Stable checkpoint exists.' if has_stable_view else 'Stable checkpoint is still missing.'}\n"
                "Recommended Next Action: Satisfy missing governance conditions before deeper progression."
            )
        else:
            session.health = "healthy" if has_stable_view else "warning"
            result = (
                "Review Result: PASS\n"
                "Admissibility: Progression is admissible.\n"
                "Health Assessment: Governance baseline checks passed.\n"
                "Open Risks:\n"
                "- No high-severity open risks currently block progression.\n"
                f"Stable View Judgment: {'Stable checkpoint exists and continuity is anchored.' if has_stable_view else 'Stable checkpoint is still missing.'}\n"
                "Recommended Next Action: Continue governed progression."
            )

        session.updated_at = datetime.utcnow().isoformat()
        self.refresh_governance(session)
        return result

    def generate_stable_view(self, session: ProjectSession) -> ProjectSession:
        accepted_outputs = [f"{t.name}: {t.result}" for t in session.tasks if t.status == "completed"]
        open_risks = [f"{r.risk_id} — {r.title}" for r in session.risk_objects if r.status == "open"]

        stable_view = LatestStableView(
            stable_step=session.current_step,
            accepted_outputs=accepted_outputs or ["No accepted outputs yet"],
            open_risks=open_risks or ["No open risks"],
            reentry_point=session.current_step,
            supervisor_note="Stable continuation anchored to current admissible step."
        )
        session.latest_stable_view = stable_view
        session.updated_at = datetime.utcnow().isoformat()
        self.refresh_governance(session)
        return session

    def closure(self, session: ProjectSession) -> tuple[ProjectSession, GateDecision, str]:
        self.refresh_governance(session)

        closure_gate = rule_registry.evaluate_as_gate("closure", "closure_gate", session)
        self._log_gate_decision(session, closure_gate, "closure")

        if not closure_gate.allowed:
            return session, closure_gate, "Closure blocked."

        completed = len([t for t in session.tasks if t.status == "completed"])
        blocked = len([t for t in session.tasks if t.status == "blocked"])
        failed = len([t for t in session.tasks if t.status == "failed"])

        session.status = "closed"
        session.updated_at = datetime.utcnow().isoformat()
        self.refresh_governance(session)

        summary = (
            f"Closure Summary\n"
            f"Project: {session.name}\n"
            f"Current Step: {session.current_step}\n"
            f"Completed Tasks: {completed}\n"
            f"Blocked Tasks: {blocked}\n"
            f"Failed Tasks: {failed}\n"
            f"Health: {session.health}\n"
            f"Status: {session.status}"
        )
        return session, closure_gate, summary

    def jump_to_step(self, session: ProjectSession, step_name: str) -> tuple[ProjectSession, GateDecision]:
        self.refresh_governance(session)

        if step_name in ["Task Execution", "Concept Layer Validation"]:
            decision = rule_registry.evaluate_as_gate(
                "deeper_progression",
                "deeper_progression_gate",
                session,
            )
            self._log_gate_decision(session, decision, f"jump_to_step:{step_name}")
            if not decision.allowed:
                return session, decision

        decision = GateDecision(
            gate_name="jump_gate",
            allowed=True,
            reason=f"Jump to '{step_name}' accepted.",
            blocking_risks=[],
        )
        self._log_gate_decision(session, decision, f"jump_to_step:{step_name}")

        session.current_step = step_name
        session.updated_at = datetime.utcnow().isoformat()
        self.refresh_governance(session)

        return session, decision

    def pause_session(self, session: ProjectSession) -> ProjectSession:
        session.status = "paused"
        session.updated_at = datetime.utcnow().isoformat()
        self.refresh_governance(session)
        return session

    def refresh_governance(self, session: ProjectSession) -> ProjectSession:
        self._generate_health_snapshot(session)
        self._generate_risk_objects(session)
        self._generate_recovery_path(session)
        return session

    def _log_gate_decision(self, session: ProjectSession, decision: GateDecision, action_name: str) -> None:
        session.gate_logs.append(
            GateLog(
                gate_name=decision.gate_name,
                allowed=decision.allowed,
                reason=decision.reason,
                blocking_risks=decision.blocking_risks.copy(),
                action_name=action_name,
            )
        )
        session.updated_at = datetime.utcnow().isoformat()

    def _generate_health_snapshot(self, session: ProjectSession) -> None:
        total_tasks = len(session.tasks)
        completed = len([t for t in session.tasks if t.status == "completed"])
        blocked = len([t for t in session.tasks if t.status == "blocked"])
        failed = len([t for t in session.tasks if t.status == "failed"])

        if blocked > 0 or failed > 0:
            overall_health = "degraded"
        elif total_tasks == 0:
            overall_health = "warning"
        else:
            overall_health = "healthy"

        session.health = overall_health
        session.health_snapshot = HealthSnapshot(
            overall_health=overall_health,
            session_status=session.status,
            current_step=session.current_step,
            total_tasks=total_tasks,
            completed_tasks=completed,
            blocked_tasks=blocked,
            failed_tasks=failed,
        )

    def _generate_risk_objects(self, session: ProjectSession) -> None:
        risks = []

        if session.agents == 0:
            risks.append(
                RiskObject(
                    risk_id="R1",
                    title="No active agents",
                    description="Execution capacity is effectively zero.",
                    severity="medium",
                    mitigation="Spawn at least one worker agent.",
                )
            )

        if len(session.tasks) == 0:
            risks.append(
                RiskObject(
                    risk_id="R2",
                    title="No task evidence",
                    description="No task outputs exist yet, so progression evidence is weak.",
                    severity="medium",
                    mitigation="Run at least one governed step before review.",
                )
            )

        if session.latest_stable_view is None:
            risks.append(
                RiskObject(
                    risk_id="R3",
                    title="No stable checkpoint",
                    description="There is no latest stable view anchoring continuity.",
                    severity="high",
                    mitigation="Generate Latest Stable View before deeper progression or closure.",
                )
            )

        if session.status == "paused":
            risks.append(
                RiskObject(
                    risk_id="R4",
                    title="Session paused",
                    description="Execution has been paused and forward work is halted.",
                    severity="low",
                    mitigation="Resume execution deliberately after review.",
                )
            )

        if session.current_step == "Goal Definition":
            risks.append(
                RiskObject(
                    risk_id="R5",
                    title="Goal drift risk",
                    description="Goal may still be under refinement and downstream work may drift.",
                    severity="medium",
                    mitigation="Review admissibility before entering deeper execution.",
                )
            )

        session.risk_objects = risks

    def _generate_recovery_path(self, session: ProjectSession) -> None:
        latest_stable_step = session.latest_stable_view.stable_step if session.latest_stable_view else "N/A"
        reentry_point = session.latest_stable_view.reentry_point if session.latest_stable_view else "create first stable checkpoint"

        if session.status == "paused":
            suggested_action = "Resume from current step or regenerate stable view before continuing."
        else:
            suggested_action = "Continue from latest admissible step."

        session.recovery_path = RecoveryPath(
            current_step=session.current_step,
            latest_stable_step=latest_stable_step,
            reentry_point=reentry_point,
            suggested_action=suggested_action,
            recovery_mode="bounded recovery",
        )


orchestrator = AARSOrchestrator()
