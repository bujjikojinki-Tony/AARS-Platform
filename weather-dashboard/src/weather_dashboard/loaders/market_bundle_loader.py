from __future__ import annotations

import json
from pathlib import Path


class MarketBundleLoader:
    def load(self, path: str | Path) -> list[dict]:
        return json.loads(Path(path).read_text(encoding="utf-8"))
