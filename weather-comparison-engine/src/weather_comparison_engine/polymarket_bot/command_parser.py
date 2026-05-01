from __future__ import annotations

from dataclasses import dataclass


SUPPORTED_COMMANDS = {
    "/run scan",
    "/show rules",
    "/set mode simulation",
    "/set mode observe_only",
}
REJECTED_PREFIXES = ("/live", "/auto", "/approve", "/promote")


@dataclass(slots=True)
class ParsedCommand:
    raw: str
    command: str
    args: list[str]


def parse_command(raw_command: str) -> ParsedCommand:
    command_text = raw_command.strip()
    if not command_text:
        raise ValueError("empty command")

    if any(command_text.startswith(prefix) for prefix in REJECTED_PREFIXES):
        raise ValueError("unsupported command: live or auto-trade commands are disabled")

    parts = command_text.split()
    if parts[:2] == ["/run", "scan"]:
        return ParsedCommand(raw=raw_command, command="run_scan", args=[])
    if parts[:1] == ["/simulate"] and len(parts) == 2:
        return ParsedCommand(raw=raw_command, command="simulate", args=[parts[1]])
    if parts[:2] == ["/show", "rules"]:
        return ParsedCommand(raw=raw_command, command="show_rules", args=[])
    if parts[:3] == ["/set", "mode", "simulation"]:
        return ParsedCommand(raw=raw_command, command="set_mode", args=["SIMULATION"])
    if parts[:3] == ["/set", "mode", "observe_only"]:
        return ParsedCommand(raw=raw_command, command="set_mode", args=["OBSERVE_ONLY"])

    raise ValueError("unsupported command")
