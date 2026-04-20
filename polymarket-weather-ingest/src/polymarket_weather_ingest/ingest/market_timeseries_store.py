from __future__ import annotations

import json
from pathlib import Path


class MarketTimeseriesStore:
    def __init__(self, path: str = "data/cache/market_timeseries.jsonl") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, payload: dict) -> None:
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
