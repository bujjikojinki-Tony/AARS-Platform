from pydantic import BaseModel


class CommandIntent(BaseModel):
    type: str
    candidate_id: str | None = None
    mode: str | None = None
    raw: str


def parse_command(text: str) -> CommandIntent:
    raw = text.strip()
    parts = raw.split()
    if raw == "/run scan":
        return CommandIntent(type="RUN_SCAN", raw=raw)
    if raw == "/list opportunities":
        return CommandIntent(type="LIST_OPPORTUNITIES", raw=raw)
    if len(parts) == 2 and parts[0] == "/simulate":
        return CommandIntent(type="SIMULATE", candidate_id=parts[1], raw=raw)
    if raw == "/simulate":
        return CommandIntent(type="INVALID", raw=raw)
    if len(parts) == 2 and parts[0] == "/block":
        return CommandIntent(type="BLOCK", candidate_id=parts[1], raw=raw)
    if len(parts) == 3 and parts[0] == "/set" and parts[1] == "mode":
        return CommandIntent(type="SET_MODE", mode=parts[2].upper(), raw=raw)
    if raw == "/show rules":
        return CommandIntent(type="SHOW_RULES", raw=raw)
    if raw == "/show history":
        return CommandIntent(type="SHOW_HISTORY", raw=raw)
    return CommandIntent(type="UNKNOWN", raw=raw)
