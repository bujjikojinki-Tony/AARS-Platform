from enum import Enum


class Side(str, Enum):
    YES = "YES"
    NO = "NO"
    WAIT = "WAIT"


class RiskStatus(str, Enum):
    PASS_ = "PASS"
    WARN = "WARN"
    BLOCK = "BLOCK"


class ActionStatus(str, Enum):
    WATCH = "WATCH"
    SIMULATE = "SIMULATE"
    APPROVE_SMALL = "APPROVE_SMALL"
    BLOCKED = "BLOCKED"
    EXECUTED = "EXECUTED"
    EXPIRED = "EXPIRED"


class ExecutionMode(str, Enum):
    OBSERVE_ONLY = "OBSERVE_ONLY"
    SIMULATION = "SIMULATION"
    PAPER_TRADE = "PAPER_TRADE"
    LIVE_EXECUTE = "LIVE_EXECUTE"


class ExecutionStatus(str, Enum):
    QUEUED = "QUEUED"
    SIMULATED = "SIMULATED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
