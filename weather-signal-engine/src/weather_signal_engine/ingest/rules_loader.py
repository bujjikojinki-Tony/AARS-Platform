import json
from pathlib import Path

from weather_signal_engine.models.rule import Rule


class RulesLoader:
    def load(self, path: str | Path) -> list[Rule]:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        rules = payload["rules"] if isinstance(payload, dict) and "rules" in payload else payload
        return [Rule(**item) for item in rules]
