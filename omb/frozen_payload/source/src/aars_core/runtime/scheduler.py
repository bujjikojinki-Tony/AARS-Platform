from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass
class ScheduledTask:
    name: str
    callback: Callable[[], None]
    interval_seconds: float
    next_run_at: float
    enabled: bool = True


@dataclass(frozen=True)
class TaskRun:
    name: str
    scheduled_at: float
    succeeded: bool
    error: str | None = None


class Scheduler:
    """Clock-driven scheduler; callers decide when run_due is invoked."""

    def __init__(self) -> None:
        self._tasks: dict[str, ScheduledTask] = {}

    def register(self, task: ScheduledTask) -> None:
        if task.name in self._tasks:
            raise ValueError(f"Task already registered: {task.name}")
        if task.interval_seconds <= 0:
            raise ValueError("interval_seconds must be positive")
        self._tasks[task.name] = task

    def set_enabled(self, name: str, enabled: bool) -> None:
        self._tasks[name].enabled = enabled

    def list_tasks(self) -> tuple[ScheduledTask, ...]:
        return tuple(self._tasks[name] for name in sorted(self._tasks))

    def run_due(self, now: float) -> tuple[TaskRun, ...]:
        results: list[TaskRun] = []
        for task in self.list_tasks():
            if not task.enabled or task.next_run_at > now:
                continue
            scheduled_at = task.next_run_at
            try:
                task.callback()
                results.append(TaskRun(task.name, scheduled_at, True))
            except Exception as exc:
                results.append(TaskRun(task.name, scheduled_at, False, str(exc)))
            while task.next_run_at <= now:
                task.next_run_at += task.interval_seconds
        return tuple(results)

