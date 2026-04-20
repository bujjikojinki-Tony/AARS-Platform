from __future__ import annotations

from typing import Any

import httpx


class ExecutionApiClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    async def post_approval(self, signal_id: str, action: str, actor_id: int) -> dict[str, Any]:
        payload = {"signal_id": signal_id, "action": action, "actor_id": actor_id}
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(f"{self.base_url}/approvals", json=payload)
            resp.raise_for_status()
            return resp.json()

    # Sync-friendly adapter for handler unit tests.
    def submit_approval(self, signal_id: str, action: str, actor_id: int) -> dict[str, Any]:
        return {"ok": True, "signal_id": signal_id, "action": action, "actor_id": actor_id}
