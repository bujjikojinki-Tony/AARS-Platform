from __future__ import annotations

import httpx


class GammaClient:
    def __init__(self, base_url: str = "https://gamma-api.polymarket.com") -> None:
        self.base_url = base_url.rstrip("/")

    def fetch_active_events_sync(self, limit: int = 20, offset: int = 0) -> list[dict]:
        url = f"{self.base_url}/events"
        params = {
            "active": "true",
            "closed": "false",
            "limit": limit,
            "offset": offset,
        }
        with httpx.Client(timeout=20) as client:
            resp = client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()

    def fetch_markets_sync(self, limit: int = 20, offset: int = 0) -> list[dict]:
        url = f"{self.base_url}/markets"
        params = {
            "active": "true",
            "closed": "false",
            "limit": limit,
            "offset": offset,
        }
        with httpx.Client(timeout=20) as client:
            resp = client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()

    def fetch_tags_sync(self) -> list[dict]:
        url = f"{self.base_url}/tags"
        with httpx.Client(timeout=20) as client:
            resp = client.get(url)
            resp.raise_for_status()
            return resp.json()

    def search_sync(self, query: str) -> dict:
        url = f"{self.base_url}/public-search"
        params = {"q": query}
        with httpx.Client(timeout=20) as client:
            resp = client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()
