from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


class JsonlLoader:
    def load_records(self, path: str | Path) -> list[dict]:
        src = Path(path)
        if not src.exists():
            return []

        records: list[dict] = []
        for line in src.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            if isinstance(payload, dict):
                records.append(payload)
        return records

    def load_df(self, path: str | Path) -> pd.DataFrame:
        return pd.DataFrame(self.load_records(path))
