from __future__ import annotations

import json
import os
from typing import TypeVar
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


T = TypeVar("T")

API_BASE = os.getenv("WEATHER_DASHBOARD_API_BASE", "http://127.0.0.1:8000").rstrip("/")


def apiGet(path: str) -> T:
    request = Request(f"{API_BASE}{path}", method="GET")
    try:
        with urlopen(request, timeout=15) as response:
            payload = response.read().decode("utf-8")
        return json.loads(payload)
    except (HTTPError, URLError) as exc:  # pragma: no cover - surface in UI
        raise RuntimeError(f"GET {path} failed: {exc}") from exc


def apiPost(path: str, body: object | None = None) -> T:
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
    request = Request(
        f"{API_BASE}{path}",
        data=data,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urlopen(request, timeout=15) as response:
            payload = response.read().decode("utf-8")
        return json.loads(payload)
    except (HTTPError, URLError) as exc:  # pragma: no cover - surface in UI
        raise RuntimeError(f"POST {path} failed: {exc}") from exc
