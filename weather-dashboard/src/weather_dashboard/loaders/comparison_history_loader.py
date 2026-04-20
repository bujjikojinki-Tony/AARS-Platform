import json
from pathlib import Path

import pandas as pd


class ComparisonHistoryLoader:
    def load_df(self, path: str | Path) -> pd.DataFrame:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return pd.DataFrame(payload)
