import json
from pathlib import Path


class StationMapLoader:
    def load(self, path: str | Path) -> list[dict]:
        return json.loads(Path(path).read_text(encoding="utf-8"))
