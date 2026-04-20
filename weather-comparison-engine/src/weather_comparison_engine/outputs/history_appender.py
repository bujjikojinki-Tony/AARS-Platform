import json
from pathlib import Path
from typing import Any


class ComparisonHistoryAppender:
    def __init__(
        self,
        path: str = "data/outputs/comparison_history.json",
        max_rows_per_market: int = 300,
    ) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.max_rows_per_market = max_rows_per_market

    def load(self) -> list[dict]:
        if not self.path.exists():
            return []
        return json.loads(self.path.read_text(encoding="utf-8"))

    def append(self, point: dict) -> bool:
        """
        Append a new point if it is meaningfully different from the last point
        of the same market.

        Returns:
            True  -> appended
            False -> skipped due to dedupe
        """
        rows = self.load()

        market_id = point.get("market_id")
        if market_id is None:
            raise ValueError("point missing market_id")

        last_same_market = self._find_last_for_market(rows, market_id)

        if last_same_market is not None and self._is_duplicate(last_same_market, point):
            return False

        rows.append(point)
        rows = self._truncate_per_market(rows)

        self.path.write_text(
            json.dumps(rows, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return True

    def overwrite_latest_dashboard_rows(
        self,
        rows: list[dict],
        path: str = "data/outputs/latest_dashboard_rows.json",
    ) -> None:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps(rows, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _find_last_for_market(self, rows: list[dict], market_id: str) -> dict | None:
        for row in reversed(rows):
            if row.get("market_id") == market_id:
                return row
        return None

    def _truncate_per_market(self, rows: list[dict]) -> list[dict]:
        """
        Keep only the most recent N rows for each market_id.
        Preserve overall chronological order of surviving rows.
        """
        buckets: dict[str, list[dict]] = {}

        for row in rows:
            market_id = row.get("market_id")
            if market_id is None:
                # keep malformed rows out of the bucket logic
                continue
            buckets.setdefault(market_id, []).append(row)

        trimmed_ids = {
            id(r)
            for bucket in buckets.values()
            for r in bucket[-self.max_rows_per_market :]
        }

        trimmed_rows = [row for row in rows if id(row) in trimmed_ids]
        return trimmed_rows

    def _is_duplicate(self, last: dict, new: dict) -> bool:
        """
        Deduplicate on meaningful comparison fields, not timestamp.
        Comparison is only within the same market_id.
        """
        keys = [
            "market_id",
            "band_scheme",
            "model_band",
            "market_band",
            "market_probability",
            "favored_side",
            "yes_price",
            "no_price",
            "comparison_status",
            "action_hint",
            "confidence_adjusted_gap",
        ]

        for key in keys:
            if not self._same_value(last.get(key), new.get(key)):
                return False

        return True

    @staticmethod
    def _same_value(a: Any, b: Any) -> bool:
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            return abs(float(a) - float(b)) < 1e-9
        return a == b
