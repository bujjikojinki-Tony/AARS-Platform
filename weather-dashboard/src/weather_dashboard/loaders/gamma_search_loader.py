from __future__ import annotations

import json
import os
import ssl
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import URLError

import certifi


class GammaSearchLoader:
    def __init__(self, base_url: str = "https://gamma-api.polymarket.com") -> None:
        self.base_url = base_url.rstrip("/")

    def search(self, query: str, limit: int = 20) -> list[dict]:
        needle = query.strip()
        if not needle:
            return []

        payload = self._fetch(needle)
        records = self._normalize_payload(payload)
        return records[:limit]

    def _fetch(self, query: str) -> object:
        url = f"{self.base_url}/public-search?{urlencode({'q': query})}"
        request = Request(url, headers={"User-Agent": "weather-dashboard/1.0"})
        try:
            with urlopen(request, timeout=15) as response:  # nosec: B310 - trusted public API
                raw = response.read().decode("utf-8")
        except URLError as exc:
            if self._is_ssl_handshake_error(exc):
                secure_retry = self._fetch_with_ca_bundle(request)
                if secure_retry is not None:
                    return secure_retry
                if self._allow_insecure_ssl():
                    return self._fetch_without_ssl_verification(request)
            raise RuntimeError(f"Gamma search failed: {exc}") from exc

        return json.loads(raw)

    def _fetch_with_ca_bundle(self, request: Request) -> object | None:
        ca_bundle = self._resolve_ca_bundle()
        if ca_bundle is None:
            return None
        context = ssl.create_default_context(cafile=str(ca_bundle))
        try:
            with urlopen(request, timeout=15, context=context) as response:  # nosec: B310 - trusted public API
                raw = response.read().decode("utf-8")
        except URLError:
            return None
        return json.loads(raw)

    def _fetch_without_ssl_verification(self, request: Request) -> object:
        context = ssl._create_unverified_context()  # noqa: SLF001, nosec: B323 - opt-in dev fallback only
        try:
            with urlopen(request, timeout=15, context=context) as response:  # nosec: B310 - opt-in dev fallback
                raw = response.read().decode("utf-8")
        except URLError as exc:
            raise RuntimeError(f"Gamma search failed after insecure SSL fallback: {exc}") from exc
        return json.loads(raw)

    @staticmethod
    def _allow_insecure_ssl() -> bool:
        return os.getenv("GAMMA_SEARCH_ALLOW_INSECURE_SSL", "").lower() in {
            "1",
            "true",
            "yes",
        }

    @staticmethod
    def _resolve_ca_bundle() -> Path | None:
        bundle = os.getenv("GAMMA_SEARCH_CA_BUNDLE", "").strip()
        if bundle:
            path = Path(bundle)
            if path.exists():
                return path
        try:
            certifi_path = Path(certifi.where())
        except Exception:
            return None
        return certifi_path if certifi_path.exists() else None

    @staticmethod
    def _is_ssl_handshake_error(exc: URLError) -> bool:
        reason = getattr(exc, "reason", None)
        if isinstance(reason, ssl.SSLCertVerificationError):
            return True
        if isinstance(reason, ssl.SSLError):
            return True
        text = str(exc)
        return any(
            token in text
            for token in [
                "CERTIFICATE_VERIFY_FAILED",
                "UNEXPECTED_EOF_WHILE_READING",
                "EOF occurred in violation of protocol",
                "SSL:",
            ]
        )

    def _normalize_payload(self, payload: object) -> list[dict]:
        records: list[dict] = []
        for index, raw in enumerate(self._iter_records(payload)):
            normalized = self._normalize_record(raw, index=index)
            if normalized.get("market_id") is not None:
                records.append(normalized)
        return records

    def _iter_records(self, payload: object) -> list[dict]:
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]

        if not isinstance(payload, dict):
            return []

        candidates: list[dict] = []
        for key in ("markets", "results", "items", "data"):
            value = payload.get(key)
            if isinstance(value, list):
                candidates.extend(item for item in value if isinstance(item, dict))
            elif isinstance(value, dict):
                candidates.append(value)

        if candidates:
            return candidates

        if any(key in payload for key in ("id", "title", "question", "slug", "market_id")):
            return [payload]

        nested: list[dict] = []
        for value in payload.values():
            nested.extend(self._iter_records(value))
        return nested

    def _normalize_record(self, raw: dict, index: int) -> dict:
        market_id = raw.get("market_id") or raw.get("id") or raw.get("slug")
        market_question = (
            raw.get("market_question")
            or raw.get("question")
            or raw.get("title")
            or raw.get("name")
            or raw.get("description")
        )
        market_family = raw.get("market_family") or raw.get("category") or "gamma"
        updated_at = (
            raw.get("updated_at")
            or raw.get("updatedAt")
            or raw.get("created_at")
            or raw.get("createdAt")
            or datetime.now(timezone.utc).isoformat()
        )

        return {
            "market_id": str(market_id) if market_id is not None else None,
            "market_question": market_question,
            "market_family": market_family,
            "location_name": raw.get("location_name") or raw.get("location"),
            "updated_at": updated_at,
            "market_band": raw.get("market_band"),
            "market_band_label": raw.get("market_band_label") or raw.get("resolution"),
            "market_band_scheme": raw.get("market_band_scheme"),
            "favored_side": raw.get("favored_side"),
            "market_probability": raw.get("market_probability"),
            "yes_price": raw.get("yes_price"),
            "no_price": raw.get("no_price"),
            "slug": raw.get("slug"),
            "active": raw.get("active"),
            "closed": raw.get("closed"),
            "search_source": "gamma",
            "search_rank": index + 1,
            "gamma_url": raw.get("url"),
            "gamma_category": raw.get("category"),
        }
