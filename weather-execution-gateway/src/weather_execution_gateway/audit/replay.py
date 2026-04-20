from pathlib import Path


class ReplayReader:
    def __init__(self, path: str = "data/outputs/audit_log.jsonl") -> None:
        self.path = Path(path)

    def exists(self) -> bool:
        return self.path.exists()
