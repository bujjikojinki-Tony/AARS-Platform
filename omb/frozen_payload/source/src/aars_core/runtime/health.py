from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class HealthResult:
    name: str
    status: str
    message: str = ""
    details: dict[str, object] | None = None


class HealthMonitor:
    VALID_STATUSES = ("HEALTHY", "DEGRADED", "UNHEALTHY")

    def __init__(self) -> None:
        self._checks: dict[str, Callable[[], HealthResult]] = {}

    def register(self, name: str, check: Callable[[], HealthResult]) -> None:
        if name in self._checks:
            raise ValueError(f"Health check already registered: {name}")
        self._checks[name] = check

    def run(self) -> tuple[HealthResult, ...]:
        results: list[HealthResult] = []
        for name in sorted(self._checks):
            try:
                result = self._checks[name]()
                if result.name != name or result.status not in self.VALID_STATUSES:
                    raise ValueError("Health check returned an invalid result")
            except Exception as exc:
                result = HealthResult(name, "UNHEALTHY", str(exc))
            results.append(result)
        return tuple(results)

    def overall_status(self, results: tuple[HealthResult, ...] | None = None) -> str:
        results = results if results is not None else self.run()
        if any(result.status == "UNHEALTHY" for result in results):
            return "UNHEALTHY"
        if any(result.status == "DEGRADED" for result in results):
            return "DEGRADED"
        return "HEALTHY"
