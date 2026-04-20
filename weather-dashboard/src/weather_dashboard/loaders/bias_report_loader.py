from pathlib import Path

import pandas as pd


class BiasReportLoader:
    def load_df(self, path: str | Path) -> pd.DataFrame:
        return pd.read_csv(path)

