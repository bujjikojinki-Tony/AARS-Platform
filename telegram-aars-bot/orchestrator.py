from datetime import datetime
from uuid import uuid4

from models import AgentTask, LatestStableView, ProjectSession


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
        return session

    def spawn_agents(self, session: ProjectSession, count: int) -> ProjectSession:
        session.agents += count
        session.updated_at = datetime.utcnow().isoformat()
        return session

    def run_step(self, session: ProjectSession, step_name: str) -> ProjectSession:
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
        return session

    def review(self, session: ProjectSession) -> str:
        if not session.tasks:
            session.health = "warning"
            return "Review Result: PASS WITH NOTES\nNo execution tasks found yet."

        session.health = "healthy"
        return (
            "Review Result: PASS WITH NOTES\n"
            "Open Risks:\n"
            "1. 当前为 mock orchestrator，尚未接入真实 GPT Supervisor\n"
            "2. 尚未接入 Codex Worker Pool\n"
            "3. 尚未接入持久化存储"
        )

    def generate_stable_view(self, session: ProjectSession) -> ProjectSession:
        accepted_outputs = [
            f"{task.name}: {task.result}"
            for task in session.tasks
            if task.status == "completed"
        ]

        stable_view = LatestStableView(
            stable_step=session.current_step,
            accepted_outputs=accepted_outputs or ["No accepted outputs yet"],
            open_risks=[
                "GPT Supervisor not connected",
                "Codex Workers not connected",
                "Persistent storage not connected",
            ],
            reentry_point=session.current_step,
            supervisor_note="Current stable view is mock-generated for MVP.",
        )
        session.latest_stable_view = stable_view
        session.updated_at = datetime.utcnow().isoformat()
        return session

    def closure(self, session: ProjectSession) -> str:
        completed = len([task for task in session.tasks if task.status == "completed"])
        blocked = len([task for task in session.tasks if task.status == "blocked"])
        failed = len([task for task in session.tasks if task.status == "failed"])

        session.status = "closed"
        session.updated_at = datetime.utcnow().isoformat()

        return (
            f"Closure Summary\n"
            f"Project: {session.name}\n"
            f"Current Step: {session.current_step}\n"
            f"Completed Tasks: {completed}\n"
            f"Blocked Tasks: {blocked}\n"
            f"Failed Tasks: {failed}\n"
            f"Health: {session.health}\n"
            f"Status: {session.status}"
        )


orchestrator = AARSOrchestrator()
