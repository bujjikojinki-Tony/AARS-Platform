from __future__ import annotations

import json
from typing import Any

from backend.models.core import MarketSnapshot
from backend.models.polymarket import PolymarketMarketRecord


class PolymarketMarketNormalizer:
    """
    Converts raw Gamma-like market payloads into PolymarketMarketRecord
    and then into internal PWB MarketSnapshot.
    Safety boundary:
    - no network
    - no wallet
    - no trading
    - pure normalization only
    """

    def normalize_market(self, raw: dict[str, Any]) -> PolymarketMarketRecord:
        outcomes = self._parse_list(raw.get("outcomes"))
        outcome_prices = self._parse_float_list(raw.get("outcomePrices") or raw.get("outcome_prices"))
        clob_token_ids = self._parse_list(raw.get("clobTokenIds") or raw.get("clob_token_ids"))
        identifier = (
            raw.get("id")
            or raw.get("marketId")
            or raw.get("market_id")
            or raw.get("conditionId")
            or raw.get("condition_id")
            or "UNKNOWN"
        )
        return PolymarketMarketRecord(
            polymarket_market_id=str(identifier),
            condition_id=raw.get("conditionId") or raw.get("condition_id"),
            question=str(raw.get("question") or raw.get("title") or ""),
            slug=raw.get("slug"),
            category=raw.get("category"),
            active=self._parse_bool(raw.get("active"), default=True),
            closed=self._parse_optional_bool(raw.get("closed")),
            archived=self._parse_optional_bool(raw.get("archived")),
            end_date=raw.get("endDate") or raw.get("end_date"),
            resolution_source=raw.get("resolutionSource") or raw.get("resolution_source"),
            outcomes=outcomes,
            outcome_prices=outcome_prices,
            clob_token_ids=clob_token_ids,
            liquidity=self._parse_optional_float(raw.get("liquidity") or raw.get("liquidityNum")),
            volume=self._parse_optional_float(raw.get("volume") or raw.get("volumeNum")),
            raw_payload=dict(raw),
            source=str(raw.get("source") or "polymarket"),
        )

    def normalize(self, raw: dict[str, Any]) -> PolymarketMarketRecord:
        return self.normalize_market(raw)

    def to_market_snapshot(
        self,
        record: PolymarketMarketRecord,
        spread: float | None = None,
    ) -> MarketSnapshot:
        return record.to_market_snapshot(spread=spread)

    def _parse_list(self, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(x) for x in value]
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return []
            try:
                parsed = json.loads(text)
                if isinstance(parsed, list):
                    return [str(x) for x in parsed]
            except Exception:
                pass
            if "," in text:
                return [x.strip() for x in text.split(",") if x.strip()]
            return [text]
        return [str(value)]

    def _parse_float_list(self, value: Any) -> list[float]:
        raw_values = self._parse_list(value)
        parsed: list[float] = []
        for item in raw_values:
            try:
                parsed.append(float(item))
            except Exception:
                continue
        return parsed

    def _parse_optional_float(self, value: Any) -> float | None:
        if value is None or value == "":
            return None
        try:
            return float(value)
        except Exception:
            return None

    def _parse_bool(self, value: Any, default: bool = False) -> bool:
        parsed = self._parse_optional_bool(value)
        if parsed is None:
            return default
        return parsed

    def _parse_optional_bool(self, value: Any) -> bool | None:
        if value is None:
            return None
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            text = value.strip().lower()
            if text in {"true", "1", "yes", "y"}:
                return True
            if text in {"false", "0", "no", "n"}:
                return False
        return None
