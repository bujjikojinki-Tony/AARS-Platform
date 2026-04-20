from __future__ import annotations

import json
from pathlib import Path


class PolymarketUserActivityReader:
    """
    Read account activity without private-key access.

    The current implementation intentionally supports local JSON snapshots and an empty stub only.
    A future authenticated reader can implement the same `get_positions` contract.
    """

    def __init__(self, source_path: str | Path | None = None) -> None:
        self.source_path = Path(source_path) if source_path else None

    def get_positions(self) -> dict:
        if self.source_path is None or not self.source_path.exists():
            return self.get_positions_stub()

        payload = json.loads(self.source_path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            payload = {"positions": payload}
        if not isinstance(payload, dict):
            payload = {"positions": []}

        payload.setdefault("positions", [])
        payload.setdefault("open_orders", [])
        payload.setdefault("balance", {})
        payload.setdefault("source", "local_account_snapshot")
        payload["source_path"] = str(self.source_path)
        return payload

    def get_positions_stub(self) -> dict:
        return {
            "source": "stub",
            "balance": {},
            "positions": [],
            "open_orders": [],
        }
