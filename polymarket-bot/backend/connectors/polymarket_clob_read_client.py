from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any

from backend.connectors.polymarket_config import PolymarketConnectorConfig
from backend.connectors.polymarket_errors import ReadOnlyConnectorInvalidResponse
from backend.connectors.polymarket_errors import ReadOnlyConnectorNetworkDisabled
from backend.connectors.polymarket_errors import ReadOnlyConnectorRequestError


class PolymarketClobReadClient:
    """
    Read-only CLOB market data client.
    Safety boundary:
    - GET only.
    - No auth.
    - No wallet.
    - No signing.
    - No order/cancel/trading methods.
    """

    def __init__(
        self,
        config: PolymarketConnectorConfig | None = None,
        *,
        allow_polymarket_network: bool | None = None,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        self.config = self._normalize_config(
            config,
            allow_polymarket_network=allow_polymarket_network,
            base_url=base_url,
            timeout_seconds=timeout_seconds,
        )
        self.config.validate_safe_defaults()

    def get_price(self, token_id: str, side: str = "BUY") -> dict[str, Any]:
        return self._get_json(
            "/price",
            {
                "token_id": token_id,
                "side": side,
            },
        )

    def get_midpoint(self, token_id: str) -> dict[str, Any]:
        return self._get_json("/midpoint", {"token_id": token_id})

    def get_spread(self, token_id: str) -> dict[str, Any]:
        return self._get_json("/spread", {"token_id": token_id})

    def get_book(self, token_id: str) -> dict[str, Any]:
        return self._get_json("/book", {"token_id": token_id})

    def get_orderbook(self, token_id: str) -> dict[str, Any]:
        return self.get_book(token_id)

    def get_prices_history(
        self,
        token_id: str,
        start_ts: int | None = None,
        end_ts: int | None = None,
        interval: str | None = None,
        fidelity: int | None = None,
    ) -> dict[str, Any]:
        query: dict[str, Any] = {"market": token_id}
        if start_ts is not None:
            query["startTs"] = int(start_ts)
        if end_ts is not None:
            query["endTs"] = int(end_ts)
        if interval is not None:
            query["interval"] = interval
        if fidelity is not None:
            query["fidelity"] = int(fidelity)
        return self._get_json("/prices-history", query)

    def get_markets(self, limit: int = 100) -> list[dict[str, Any]]:
        return self._get_list("/markets", {"limit": max(1, int(limit))})

    def get_market(self, market_id: str) -> dict[str, Any]:
        return self._get_json(f"/markets/{market_id}")

    def _get_list(self, path: str, query: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        payload = self._get_json(path, query)
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            for key in ("data", "results", "markets"):
                value = payload.get(key)
                if isinstance(value, list):
                    return value
        raise ReadOnlyConnectorInvalidResponse(
            f"expected list-like response from CLOB {path}"
        )

    def _get_json(self, path: str, query: dict[str, Any] | None = None) -> Any:
        if not self.config.allow_polymarket_network:
            raise ReadOnlyConnectorNetworkDisabled(
                "Polymarket CLOB network access disabled by config."
            )
        url = self._build_url(path, query or {})
        request = urllib.request.Request(
            url=url,
            method="GET",
            headers={
                "Accept": "application/json",
                "User-Agent": "pwb-read-only-connector-v0",
            },
        )
        try:
            with urllib.request.urlopen(
                request,
                timeout=self.config.request_timeout_seconds,
            ) as response:
                body = response.read().decode("utf-8")
                return json.loads(body)
        except ReadOnlyConnectorInvalidResponse:
            raise
        except ReadOnlyConnectorNetworkDisabled:
            raise
        except json.JSONDecodeError as exc:
            raise ReadOnlyConnectorInvalidResponse(
                f"CLOB GET {path} returned invalid JSON: {exc}"
            ) from exc
        except Exception as exc:
            raise ReadOnlyConnectorRequestError(f"CLOB GET {path} failed: {exc}") from exc

    def _build_url(self, path: str, query: dict[str, Any]) -> str:
        base = self.config.clob_base_url.rstrip("/")
        normalized_path = "/" + path.strip("/")
        encoded = urllib.parse.urlencode(query)
        return f"{base}{normalized_path}?{encoded}" if encoded else f"{base}{normalized_path}"

    def _normalize_config(
        self,
        config: PolymarketConnectorConfig | None,
        *,
        allow_polymarket_network: bool | None,
        base_url: str | None,
        timeout_seconds: float | None,
    ) -> PolymarketConnectorConfig:
        if config is None:
            return PolymarketConnectorConfig(
                allow_polymarket_network=(
                    False if allow_polymarket_network is None else allow_polymarket_network
                ),
                clob_base_url=base_url or "https://clob.polymarket.com",
                request_timeout_seconds=timeout_seconds or 8.0,
            )
        updates: dict[str, Any] = {}
        if allow_polymarket_network is not None:
            updates["allow_polymarket_network"] = allow_polymarket_network
        if base_url is not None:
            updates["clob_base_url"] = base_url
        if timeout_seconds is not None:
            updates["request_timeout_seconds"] = timeout_seconds
        return config.model_copy(update=updates) if updates else config
