import json
from glob import glob
from pathlib import Path


class RealtimeForecastLoader:
    def load(self, path: str | Path) -> dict:
        return json.loads(Path(path).read_text(encoding="utf-8"))

    def load_many(self, pattern_or_path: str | Path) -> list[dict]:
        pattern = str(pattern_or_path)
        paths: list[str] = []

        if any(char in pattern for char in "*?[]"):
            paths = sorted(glob(pattern))
        else:
            candidate = Path(pattern)
            if candidate.is_dir():
                paths = sorted(str(path) for path in candidate.glob("forecast_realtime_snapshot_*.json"))
            elif candidate.exists():
                paths = [pattern]

        snapshots = [self.load(path) for path in paths]
        snapshots.sort(
            key=lambda snapshot: (
                str(snapshot.get("timestamp") or ""),
                str(snapshot.get("market_id") or ""),
            ),
            reverse=True,
        )
        return snapshots
