from dataclasses import dataclass, field, asdict
from typing import List, Optional
from datetime import datetime


@dataclass
class AgentTask:
    task_id: str
    name: str
    agent_type: str
    status: str = "pending"
    result: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    @staticmethod
    def from_dict(data: dict) -> "AgentTask":
        return AgentTask(**data)


@dataclass
class LatestStableView:
    stable_step: str
    accepted_outputs: List[str]
    open_risks: List[str]
    reentry_point: str
    supervisor_note: str

    @staticmethod
    def from_dict(data: dict) -> "LatestStableView":
        return LatestStableView(**data)


@dataclass
class HealthSnapshot:
    overall_health: str
    session_status: str
    current_step: str
    total_tasks: int
    completed_tasks: int
    blocked_tasks: int
    failed_tasks: int
    generated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    @staticmethod
    def from_dict(data: dict) -> "HealthSnapshot":
        return HealthSnapshot(**data)


@dataclass
class RiskObject:
    risk_id: str
    title: str
    description: str
    severity: str
    mitigation: str
    status: str = "open"

    @staticmethod
    def from_dict(data: dict) -> "RiskObject":
        return RiskObject(**data)


@dataclass
class RecoveryPath:
    current_step: str
    latest_stable_step: str
    reentry_point: str
    suggested_action: str
    recovery_mode: str
    generated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    @staticmethod
    def from_dict(data: dict) -> "RecoveryPath":
        return RecoveryPath(**data)


@dataclass
class GateDecision:
    gate_name: str
    allowed: bool
    reason: str
    blocking_risks: List[str] = field(default_factory=list)

    @staticmethod
    def from_dict(data: dict) -> "GateDecision":
        return GateDecision(**data)


@dataclass
class GateLog:
    gate_name: str
    allowed: bool
    reason: str
    blocking_risks: List[str]
    action_name: str
    generated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    @staticmethod
    def from_dict(data: dict) -> "GateLog":
        return GateLog(**data)


@dataclass
class RuleResult:
    rule_name: str
    passed: bool
    severity: str
    message: str
    blocking_risks: List[str] = field(default_factory=list)


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

    health_snapshot: Optional[HealthSnapshot] = None
    risk_objects: List[RiskObject] = field(default_factory=list)
    recovery_path: Optional[RecoveryPath] = None
    gate_logs: List[GateLog] = field(default_factory=list)

    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "ProjectSession":
        return ProjectSession(
            project_id=data["project_id"],
            name=data["name"],
            current_step=data.get("current_step", "Intent Framing"),
            health=data.get("health", "healthy"),
            status=data.get("status", "active"),
            agents=data.get("agents", 0),
            tasks=[AgentTask.from_dict(x) for x in data.get("tasks", [])],
            latest_stable_view=LatestStableView.from_dict(data["latest_stable_view"])
            if data.get("latest_stable_view") else None,
            health_snapshot=HealthSnapshot.from_dict(data["health_snapshot"])
            if data.get("health_snapshot") else None,
            risk_objects=[RiskObject.from_dict(x) for x in data.get("risk_objects", [])],
            recovery_path=RecoveryPath.from_dict(data["recovery_path"])
            if data.get("recovery_path") else None,
            gate_logs=[GateLog.from_dict(x) for x in data.get("gate_logs", [])],
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
            updated_at=data.get("updated_at", datetime.utcnow().isoformat()),
        )
