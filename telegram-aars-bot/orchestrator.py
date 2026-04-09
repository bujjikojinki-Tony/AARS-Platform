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
)


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

        # Stable Gate + Risk Gate for deeper steps
        if step_name in ["Task Execution", "Concept Layer Validation"]:
            stable_gate = self.evaluate_stable_gate(session)
            if not stable_gate.allowed:
                return session, stable_gate

            risk_gate = self.evaluate_risk_gate(session)
            if not risk_gate.allowed:
                return session, risk_gate

        task = AgentTask(
            task_id=f"task-{uuid4().hex[:8]}",
            name=step_name,
            agent_type="builder",
            status="completed",
            result=f"{step_name} completed"
        )
        session.tasks.append(task)
        session.current_step = step_name
        session.updated_at = datetime.utcnow().isoformat()
        self.refresh_governance(session)

        return session, GateDecision(
            gate_name="execution_gate",
            allowed=True,
            reason=f"Step '{step_name}' accepted and completed.",
            blocking_risks=[],
        )

    def review(self, session: ProjectSession) -> str:
        if not session.tasks:
            session.health = "warning"
            result = (
                "Review Result: PASS WITH NOTES\n"
                "No execution tasks found yet."
            )
        else:
            session.health = "healthy"
            result = (
                "Review Result: PASS WITH NOTES\n"
                "Governance objects refreshed.\n"
                "Admissibility should be checked through gates before deeper progression."
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

        closure_gate = self.evaluate_closure_gate(session)
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

        # deeper jumps also gated
        if step_name in ["Task Execution", "Concept Layer Validation"]:
            stable_gate = self.evaluate_stable_gate(session)
            if not stable_gate.allowed:
                return session, stable_gate

            risk_gate = self.evaluate_risk_gate(session)
            if not risk_gate.allowed:
                return session, risk_gate

        session.current_step = step_name
        session.updated_at = datetime.utcnow().isoformat()
        self.refresh_governance(session)

        return session, GateDecision(
            gate_name="jump_gate",
            allowed=True,
            reason=f"Jump to '{step_name}' accepted.",
            blocking_risks=[],
        )

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

    def evaluate_stable_gate(self, session: ProjectSession) -> GateDecision:
        if session.latest_stable_view is None:
            return GateDecision(
                gate_name="stable_gate",
                allowed=False,
                reason="No Latest Stable View exists. Deeper progression is not admissible.",
                blocking_risks=["R3"],
            )

        return GateDecision(
            gate_name="stable_gate",
            allowed=True,
            reason="Stable checkpoint exists.",
            blocking_risks=[],
        )

    def evaluate_risk_gate(self, session: ProjectSession) -> GateDecision:
        blocking = [r.risk_id for r in session.risk_objects if r.severity == "high" and r.status == "open"]
        if blocking:
            return GateDecision(
                gate_name="risk_gate",
                allowed=False,
                reason="High-severity open risks exist.",
                blocking_risks=blocking,
            )

        return GateDecision(
            gate_name="risk_gate",
            allowed=True,
            reason="No high/open risks blocking progression.",
            blocking_risks=[],
        )

    def evaluate_closure_gate(self, session: ProjectSession) -> GateDecision:
        if session.latest_stable_view is None:
            return GateDecision(
                gate_name="closure_gate",
                allowed=False,
                reason="Closure requires an existing Latest Stable View.",
                blocking_risks=["R3"],
            )

        high_open = [r.risk_id for r in session.risk_objects if r.severity == "high" and r.status == "open"]
        if high_open:
            return GateDecision(
                gate_name="closure_gate",
                allowed=False,
                reason="Closure blocked by high/open risks.",
                blocking_risks=high_open,
            )

        completed = len([t for t in session.tasks if t.status == "completed"])
        if completed == 0:
            return GateDecision(
                gate_name="closure_gate",
                allowed=False,
                reason="Closure requires at least one completed task.",
                blocking_risks=[],
            )

        return GateDecision(
            gate_name="closure_gate",
            allowed=True,
            reason="Closure admissible.",
            blocking_risks=[],
        )

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
