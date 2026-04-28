from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from weather_comparison_engine.settings import (
    COMPARISON_HISTORY_JSON,
    LATEST_DASHBOARD_ROWS_JSON,
    MARKET_ALERT_EVENTS_DIR,
    MARKET_ANOMALY_EVENTS_DIR,
    OFFICIAL_HISTORY_JSONL,
    REALTIME_FORECAST_JSON,
    REALTIME_MARKET_JSON,
    RESOLVER_REPORT_JSON,
    SOURCE_POLICY_REGISTRY_JSON,
    SOURCE_POLICY_STATUS_JSON,
    VALIDATION_FRESHNESS_STATUS_JSON,
)
from weather_comparison_engine.source_policy.registry import load_source_policy_registry

SOURCE_POLICY_STATUS_SCHEMA_VERSION = "source_policy_status.v1"
WORKSPACE_DIR = Path(__file__).resolve().parents[4]


class SourcePolicyStatusBuilder:
    def __init__(
        self,
        *,
        now: datetime | None = None,
        registry_path: str | Path | None = None,
        source_inputs: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        self.now = now or datetime.now(timezone.utc)
        self.registry_path = Path(registry_path or SOURCE_POLICY_REGISTRY_JSON)
        self.source_inputs = source_inputs or _default_source_inputs()

    def build(self) -> dict:
        registry = load_source_policy_registry(self.registry_path)
        sources: list[dict] = []
        for source in registry.get("sources") or []:
            if not isinstance(source, dict):
                continue
            source_name = str(source.get("source_name") or "").strip()
            source_input = self.source_inputs.get(source_name, {})
            source_payload = _load_source_payload(source_input)
            freshness = _compute_freshness(
                source_payload=source_payload,
                source_input=source_input,
                source_policy=source,
                now=self.now,
            )
            sources.append(
                {
                    "source_name": source_name,
                    "source_type": str(source.get("source_type") or "-"),
                    "primary_use": str(source.get("primary_use") or "-"),
                    "trigger_mode": str(source.get("trigger_mode") or "-"),
                    "selected_market_poll_interval": source.get("selected_market_poll_interval"),
                    "watchlist_poll_interval": source.get("watchlist_poll_interval"),
                    "family_scan_interval": source.get("family_scan_interval"),
                    "write_interval": str(source.get("write_interval") or "-"),
                    "fresh_threshold": str(source.get("fresh_threshold") or "-"),
                    "stale_threshold": str(source.get("stale_threshold") or "-"),
                    "priority_level": str(source.get("priority_level") or "low"),
                    "fallback_policy": str(source.get("fallback_policy") or "-"),
                    "status": str(source.get("status") or "draft"),
                    "version": str(source.get("version") or "v1"),
                    "notes": str(source.get("notes") or "-"),
                    "observed_path": freshness["observed_path"],
                    "observed_at": freshness["observed_at"],
                    "age_seconds": freshness["age_seconds"],
                    "freshness_status": freshness["freshness_status"],
                    "status_reason": freshness["status_reason"],
                    "policy_threshold_seconds": freshness["policy_threshold_seconds"],
                    "stale_threshold_seconds": freshness["stale_threshold_seconds"],
                }
            )

        counts = Counter(source["freshness_status"] for source in sources)
        priority_counts = Counter(source["priority_level"] for source in sources)
        problem_sources = [
            source
            for source in sources
            if source["freshness_status"] in {"stale", "unavailable"}
        ]
        overall_status = _overall_status(sources)
        return {
            "schema_version": SOURCE_POLICY_STATUS_SCHEMA_VERSION,
            "generated_at": self.now.isoformat(),
            "registry_schema_version": str(registry.get("schema_version") or "-"),
            "overall_status": overall_status,
            "counts": {
                "fresh": counts.get("fresh", 0),
                "stale": counts.get("stale", 0),
                "unavailable": counts.get("unavailable", 0),
            },
            "priority_counts": dict(priority_counts),
            "problem_sources": problem_sources[:10],
            "sources": sources,
        }

    def write(self, path: str | Path | None = None) -> Path:
        out = Path(path or SOURCE_POLICY_STATUS_JSON)
        out.parent.mkdir(parents=True, exist_ok=True)
        payload = self.build()
        out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return out


def build_source_policy_status(
    *,
    now: datetime | None = None,
    registry_path: str | Path | None = None,
    source_inputs: dict[str, dict[str, Any]] | None = None,
    path: str | Path | None = None,
) -> dict:
    builder = SourcePolicyStatusBuilder(
        now=now,
        registry_path=registry_path,
        source_inputs=source_inputs,
    )
    payload = builder.build()
    if path is not None:
        builder.write(path)
    return payload


def _default_source_inputs() -> dict[str, dict[str, Any]]:
    return {
        "polymarket_clob": {
            "path": REALTIME_MARKET_JSON,
            "timestamp_keys": ("updated_at", "generated_at", "timestamp", "created_at"),
        },
        "polymarket_gamma": {
            "path": REALTIME_MARKET_JSON,
            "timestamp_keys": ("updated_at", "generated_at", "timestamp", "created_at"),
        },
        "resolver_registry": {
            "path": RESOLVER_REPORT_JSON,
            "timestamp_keys": ("generated_at", "updated_at", "timestamp"),
        },
        "hrrr": {
            "path": REALTIME_FORECAST_JSON,
            "timestamp_keys": ("forecast_timestamp", "timestamp", "generated_at", "updated_at"),
        },
        "ecmwf": {
            "path": REALTIME_FORECAST_JSON,
            "timestamp_keys": ("forecast_timestamp", "timestamp", "generated_at", "updated_at"),
        },
        "wunderground_station": {
            "path": WORKSPACE_DIR / "weather-dashboard" / "data" / "outputs" / "wunderground_shanghai_snapshot.json",
            "timestamp_keys": ("updated_at", "generated_at", "timestamp", "observed_at"),
        },
        "metar": {
            "path": WORKSPACE_DIR / "weather-dashboard" / "data" / "outputs" / "wunderground_shanghai_snapshot.json",
            "timestamp_keys": ("updated_at", "generated_at", "timestamp", "observed_at"),
        },
        "official_obs": {
            "path": OFFICIAL_HISTORY_JSONL,
            "timestamp_keys": ("generated_at", "timestamp", "updated_at", "observed_at"),
        },
        "climate_index_source": {
            "path": None,
            "timestamp_keys": ("generated_at", "timestamp", "updated_at"),
        },
        "sea_ice_dataset": {
            "path": None,
            "timestamp_keys": ("generated_at", "timestamp", "updated_at"),
        },
        "comparison_engine": {
            "path": LATEST_DASHBOARD_ROWS_JSON,
            "timestamp_keys": ("generated_at", "timestamp", "updated_at"),
        },
        "observation_alert_layer": {
            "path": MARKET_ALERT_EVENTS_DIR,
            "timestamp_keys": ("generated_at", "timestamp", "updated_at"),
        },
        "family_scanner": {
            "path": MARKET_ANOMALY_EVENTS_DIR,
            "timestamp_keys": ("generated_at", "timestamp", "updated_at"),
        },
        "validation_status": {
            "path": VALIDATION_FRESHNESS_STATUS_JSON,
            "timestamp_keys": ("generated_at", "timestamp", "updated_at"),
        },
        "comparison_history": {
            "path": COMPARISON_HISTORY_JSON,
            "timestamp_keys": ("generated_at", "timestamp", "updated_at"),
        },
    }


def _load_source_payload(source_input: dict[str, Any]) -> tuple[Any, Path | None]:
    path = source_input.get("path")
    if not isinstance(path, Path):
        path = Path(str(path)) if path else None
    if path is None:
        return None, None
    if path.is_dir():
        candidates = sorted([item for item in path.iterdir() if item.is_file()], key=lambda item: item.stat().st_mtime, reverse=True)
        if not candidates:
            return None, path
        path = candidates[0]
    if not path.exists():
        return None, path
    try:
        if source_input.get("kind") == "jsonl" or path.suffix == ".jsonl":
            lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
            if not lines:
                return None, path
            return json.loads(lines[-1]), path
        return json.loads(path.read_text(encoding="utf-8")), path
    except Exception:
        return None, path


def _compute_freshness(
    *,
    source_payload: tuple[Any, Path | None],
    source_input: dict[str, Any],
    source_policy: dict,
    now: datetime,
) -> dict:
    payload, path = source_payload
    if payload is None:
        return {
            "observed_path": str(path) if path else "-",
            "observed_at": None,
            "age_seconds": None,
            "freshness_status": "unavailable",
            "status_reason": "source_missing",
            "policy_threshold_seconds": _parse_duration_seconds(source_policy.get("fresh_threshold")),
            "stale_threshold_seconds": _parse_duration_seconds(source_policy.get("stale_threshold")),
        }

    observed_at = _extract_timestamp(payload, source_input.get("timestamp_keys"))
    if observed_at is None and path is not None and path.exists():
        observed_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    age_seconds = max((now - observed_at).total_seconds(), 0.0) if observed_at is not None else None
    fresh_threshold = _parse_duration_seconds(source_policy.get("fresh_threshold"))
    stale_threshold = _parse_duration_seconds(source_policy.get("stale_threshold"))
    freshness_status, status_reason = _classify_age(age_seconds, fresh_threshold, stale_threshold)
    return {
        "observed_path": str(path) if path else "-",
        "observed_at": observed_at.isoformat() if observed_at is not None else None,
        "age_seconds": age_seconds,
        "freshness_status": freshness_status,
        "status_reason": status_reason,
        "policy_threshold_seconds": fresh_threshold,
        "stale_threshold_seconds": stale_threshold,
    }


def _extract_timestamp(payload: Any, timestamp_keys: Any) -> datetime | None:
    keys = [str(item) for item in timestamp_keys or [] if item]
    if isinstance(payload, dict):
        for key in keys + ["generated_at", "updated_at", "timestamp", "created_at", "observed_at"]:
            parsed = _parse_iso(payload.get(key))
            if parsed is not None:
                return parsed
    if isinstance(payload, list):
        parsed_rows: list[datetime] = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            for key in keys + ["generated_at", "updated_at", "timestamp", "created_at", "observed_at"]:
                parsed = _parse_iso(item.get(key))
                if parsed is not None:
                    parsed_rows.append(parsed)
                    break
        if parsed_rows:
            return max(parsed_rows)
    return None


def _parse_iso(value: Any) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _parse_duration_seconds(value: Any) -> int | None:
    if value in (None, "", "-"):
        return None
    text = str(value).strip().lower()
    if not text:
        return None
    if "-" in text and not re.search(r"\d-\d", text):
        text = text.split("-", 1)[-1]
    match = re.fullmatch(r"(?P<value>\d+(?:\.\d+)?)(?P<unit>[smhd])", text)
    if not match:
        return None
    magnitude = float(match.group("value"))
    unit = match.group("unit")
    if unit == "s":
        return int(magnitude)
    if unit == "m":
        return int(magnitude * 60)
    if unit == "h":
        return int(magnitude * 3600)
    if unit == "d":
        return int(magnitude * 86400)
    return None


def _classify_age(
    age_seconds: float | None,
    fresh_threshold_seconds: int | None,
    stale_threshold_seconds: int | None,
) -> tuple[str, str]:
    if age_seconds is None:
        return "unavailable", "timestamp_missing"
    if fresh_threshold_seconds is None or stale_threshold_seconds is None:
        return "unavailable", "policy_threshold_missing"
    if age_seconds <= float(fresh_threshold_seconds):
        return "fresh", "within_fresh_threshold"
    if age_seconds <= float(stale_threshold_seconds):
        return "stale", "past_fresh_threshold"
    return "unavailable", "past_stale_threshold"


def _overall_status(sources: list[dict]) -> str:
    priority_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    has_blocked = False
    has_degraded = False
    has_warning = False
    for source in sources:
        status = str(source.get("freshness_status") or "unavailable")
        priority = str(source.get("priority_level") or "low")
        score = priority_rank.get(priority, 3)
        if status == "fresh":
            continue
        if status == "unavailable":
            if score <= 1:
                has_blocked = True
            elif score == 2:
                has_degraded = True
            else:
                has_warning = True
            continue
        if status == "stale":
            if score <= 1:
                has_degraded = True
            else:
                has_warning = True
            continue
        has_warning = True
    if has_blocked:
        return "blocked"
    if has_degraded:
        return "degraded"
    if has_warning:
        return "warning"
    return "healthy"
