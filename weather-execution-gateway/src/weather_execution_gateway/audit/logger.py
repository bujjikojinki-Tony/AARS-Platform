import json
from pathlib import Path

from weather_execution_gateway.models.audit_event import AuditEvent


class AuditLogger:
    def __init__(self, path: str = "data/outputs/audit_log.jsonl") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, event: AuditEvent) -> None:
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event.model_dump(), ensure_ascii=False) + "\n")
