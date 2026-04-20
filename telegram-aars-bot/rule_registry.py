from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Dict, List
from models import RuleResult, GateDecision


RuleFn = Callable[[object], RuleResult]


@dataclass
class RuleEntry:
    group: str
    name: str
    fn: RuleFn
    enabled: bool = True
    priority: int = 100


@dataclass
class RuleChangeLogEntry:
    rule_name: str
    group: str
    field_name: str
    old_value: str
    new_value: str
    action_name: str
    changed_at: str


class RuleRegistry:
    def __init__(self) -> None:
        self._groups: Dict[str, List[RuleEntry]] = {}
        self._by_name: Dict[str, RuleEntry] = {}
        self._change_logs: List[RuleChangeLogEntry] = []

    def register(self, group: str, fn: RuleFn, enabled: bool = True, priority: int = 100) -> None:
        entry = RuleEntry(
            group=group,
            name=fn.__name__,
            fn=fn,
            enabled=enabled,
            priority=priority,
        )
        self._groups.setdefault(group, []).append(entry)
        self._by_name[entry.name] = entry

    def evaluate(self, group: str, session) -> List[RuleResult]:
        entries = sorted(self._groups.get(group, []), key=lambda x: x.priority)
        results = []
        for entry in entries:
            if not entry.enabled:
                continue
            results.append(entry.fn(session))
        return results

    def evaluate_as_gate(self, group: str, gate_name: str, session) -> GateDecision:
        results = self.evaluate(group, session)

        failed = [r for r in results if not r.passed]
        if failed:
            blocking_risks = []
            messages = []
            for r in failed:
                blocking_risks.extend(r.blocking_risks)
                messages.append(f"{r.rule_name}: {r.message}")

            return GateDecision(
                gate_name=gate_name,
                allowed=False,
                reason=" | ".join(messages),
                blocking_risks=blocking_risks,
            )

        pass_messages = [r.message for r in results if r.passed]
        return GateDecision(
            gate_name=gate_name,
            allowed=True,
            reason=" | ".join(pass_messages) if pass_messages else f"{gate_name} passed.",
            blocking_risks=[],
        )

    def list_groups(self) -> List[str]:
        return list(self._groups.keys())

    def describe_group(self, group: str) -> List[str]:
        entries = sorted(self._groups.get(group, []), key=lambda x: x.priority)
        return [e.name for e in entries]

    def inspect_group(self, group: str, session) -> dict:
        entries = sorted(self._groups.get(group, []), key=lambda x: x.priority)
        results = []
        for entry in entries:
            if entry.enabled:
                results.append(entry.fn(session))
            else:
                results.append(
                    RuleResult(
                        rule_name=entry.name,
                        passed=True,
                        severity="disabled",
                        message="Rule disabled; skipped.",
                        blocking_risks=[],
                    )
                )

        return {
            "group": group,
            "rules": [e.name for e in entries],
            "results": results,
        }

    def list_rule_entries(self) -> List[dict]:
        entries = []
        for group_entries in self._groups.values():
            for e in group_entries:
                entries.append(
                    {
                        "group": e.group,
                        "name": e.name,
                        "enabled": e.enabled,
                        "priority": e.priority,
                    }
                )
        entries.sort(key=lambda x: (x["group"], x["priority"], x["name"]))
        return entries

    def set_rule_enabled(self, rule_name: str, enabled: bool, action_name: str = "set_rule_enabled") -> bool:
        entry = self._by_name.get(rule_name)
        if not entry:
            return False

        old_value = str(entry.enabled)
        new_value = str(enabled)

        if old_value != new_value:
            self._record_change(
                rule_name=entry.name,
                group=entry.group,
                field_name="enabled",
                old_value=old_value,
                new_value=new_value,
                action_name=action_name,
            )

        entry.enabled = enabled
        return True

    def toggle_rule(self, rule_name: str, action_name: str = "toggle_rule") -> bool:
        entry = self._by_name.get(rule_name)
        if not entry:
            return False

        old_value = str(entry.enabled)
        entry.enabled = not entry.enabled
        new_value = str(entry.enabled)

        self._record_change(
            rule_name=entry.name,
            group=entry.group,
            field_name="enabled",
            old_value=old_value,
            new_value=new_value,
            action_name=action_name,
        )
        return True

    def export_config(self) -> dict:
        return {
            "rules": [
                {
                    "group": e.group,
                    "name": e.name,
                    "enabled": e.enabled,
                    "priority": e.priority,
                }
                for e in self._by_name.values()
            ]
        }

    def import_config(self, config: dict) -> None:
        rules = config.get("rules", [])
        for item in rules:
            name = item.get("name")
            entry = self._by_name.get(name)
            if not entry:
                continue
            if "enabled" in item:
                entry.enabled = bool(item["enabled"])
            if "priority" in item:
                entry.priority = int(item["priority"])

    def export_change_logs(self) -> dict:
        return {
            "logs": [
                {
                    "rule_name": x.rule_name,
                    "group": x.group,
                    "field_name": x.field_name,
                    "old_value": x.old_value,
                    "new_value": x.new_value,
                    "action_name": x.action_name,
                    "changed_at": x.changed_at,
                }
                for x in self._change_logs
            ]
        }

    def import_change_logs(self, payload: dict) -> None:
        logs = payload.get("logs", [])
        self._change_logs = [
            RuleChangeLogEntry(
                rule_name=x["rule_name"],
                group=x["group"],
                field_name=x["field_name"],
                old_value=x["old_value"],
                new_value=x["new_value"],
                action_name=x["action_name"],
                changed_at=x["changed_at"],
            )
            for x in logs
        ]

    def list_change_logs(self, limit: int = 10) -> List[RuleChangeLogEntry]:
        return list(reversed(self._change_logs[-limit:]))

    def _record_change(
        self,
        rule_name: str,
        group: str,
        field_name: str,
        old_value: str,
        new_value: str,
        action_name: str,
    ) -> None:
        self._change_logs.append(
            RuleChangeLogEntry(
                rule_name=rule_name,
                group=group,
                field_name=field_name,
                old_value=old_value,
                new_value=new_value,
                action_name=action_name,
                changed_at=datetime.utcnow().isoformat(),
            )
        )


def rule_requires_stable_view(session) -> RuleResult:
    if session.latest_stable_view is None:
        return RuleResult(
            rule_name="requires_stable_view",
            passed=False,
            severity="high",
            message="No Latest Stable View exists.",
            blocking_risks=["R3"],
        )
    return RuleResult(
        rule_name="requires_stable_view",
        passed=True,
        severity="info",
        message="Latest Stable View exists.",
    )


def rule_no_high_open_risks(session) -> RuleResult:
    blocking = [r.risk_id for r in session.risk_objects if r.severity == "high" and r.status == "open"]
    if blocking:
        return RuleResult(
            rule_name="no_high_open_risks",
            passed=False,
            severity="high",
            message="High-severity open risks exist.",
            blocking_risks=blocking,
        )
    return RuleResult(
        rule_name="no_high_open_risks",
        passed=True,
        severity="info",
        message="No high-severity open risks block progression.",
    )


def rule_has_completed_task(session) -> RuleResult:
    completed = len([t for t in session.tasks if t.status == "completed"])
    if completed == 0:
        return RuleResult(
            rule_name="has_completed_task",
            passed=False,
            severity="medium",
            message="No completed task exists yet.",
            blocking_risks=[],
        )
    return RuleResult(
        rule_name="has_completed_task",
        passed=True,
        severity="info",
        message="At least one completed task exists.",
    )


def rule_has_execution_evidence(session) -> RuleResult:
    total = len(session.tasks)
    if total == 0:
        return RuleResult(
            rule_name="has_execution_evidence",
            passed=False,
            severity="medium",
            message="No execution evidence exists yet.",
            blocking_risks=["R2"],
        )
    return RuleResult(
        rule_name="has_execution_evidence",
        passed=True,
        severity="info",
        message="Execution evidence exists.",
    )


def rule_not_paused(session) -> RuleResult:
    if session.status == "paused":
        return RuleResult(
            rule_name="not_paused",
            passed=False,
            severity="low",
            message="Session is paused.",
            blocking_risks=["R4"],
        )
    return RuleResult(
        rule_name="not_paused",
        passed=True,
        severity="info",
        message="Session is active.",
    )


rule_registry = RuleRegistry()

rule_registry.register("deeper_progression", rule_requires_stable_view, enabled=True, priority=10)
rule_registry.register("deeper_progression", rule_no_high_open_risks, enabled=True, priority=20)
rule_registry.register("deeper_progression", rule_not_paused, enabled=True, priority=30)

rule_registry.register("closure", rule_requires_stable_view, enabled=True, priority=10)
rule_registry.register("closure", rule_no_high_open_risks, enabled=True, priority=20)
rule_registry.register("closure", rule_has_completed_task, enabled=True, priority=30)

rule_registry.register("review", rule_has_execution_evidence, enabled=True, priority=10)
rule_registry.register("review", rule_not_paused, enabled=True, priority=20)
