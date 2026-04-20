import json
from pathlib import Path


class RealtimeMarketLoader:
    def load(self, path: str | Path) -> dict:
        return json.loads(Path(path).read_text(encoding="utf-8"))
