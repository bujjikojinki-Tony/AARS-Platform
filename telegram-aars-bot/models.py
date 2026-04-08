from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class AgentTask:
    task_id: str
    name: str
    agent_type: str
    status: str = "pending"
    result: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class LatestStableView:
    stable_step: str
    accepted_outputs: List[str]
    open_risks: List[str]
    reentry_point: str
    supervisor_note: str


@dataclass
class ProjectSession:
    project_id: str
    name: str
    current_step: str = "Intent Framing"
    health: str = "healthy"
    status: str = "active"
    agents: int = 0
    tasks: List[AgentTask] = field(default_factory=list)
    latest_stable_view: Optional[LatestStableView] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
