from dataclasses import dataclass, field


@dataclass(frozen=True)
class GateResult:
    passed: bool
    status: str
    block_reasons: list[str] = field(default_factory=list)
    execution_constraint: str | None = None

