import httpx


class PolymarketRestClient:
    def __init__(self, base_url: str = "https://clob.polymarket.com") -> None:
        self.base_url = base_url.rstrip("/")

    async def healthcheck(self) -> dict:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(f"{self.base_url}/")
            return {"status_code": resp.status_code}
