from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from weather_comparison_engine.source_policy import SourcePolicyStatusBuilder


def test_source_policy_status_builder_classifies_fresh_stale_and_unavailable(tmp_path: Path) -> None:
    fresh_path = tmp_path / "fresh.json"
    stale_path = tmp_path / "stale.json"
    missing_path = tmp_path / "missing.json"

    fresh_path.write_text('{"generated_at":"2026-04-21T09:55:00+00:00"}', encoding="utf-8")
    stale_path.write_text('{"generated_at":"2026-04-21T08:30:00+00:00"}', encoding="utf-8")

    registry_path = tmp_path / "source_policy_registry.json"
    registry_path.write_text(
        json.dumps(
            {
                "schema_version": "source_policy_registry.v1",
                "sources": [
                    {
                        "source_name": "fresh_source",
                        "source_type": "market_realtime",
                        "primary_use": "fresh source",
                        "trigger_mode": "poll",
                        "write_interval": "1m",
                        "fresh_threshold": "30m",
                        "stale_threshold": "90m",
                        "priority_level": "critical",
                        "fallback_policy": "fallback",
                        "status": "active",
                        "version": "v1",
                    },
                    {
                        "source_name": "stale_source",
                        "source_type": "forecast_synoptic",
                        "primary_use": "stale source",
                        "trigger_mode": "poll",
                        "write_interval": "1m",
                        "fresh_threshold": "30m",
                        "stale_threshold": "90m",
                        "priority_level": "high",
                        "fallback_policy": "fallback",
                        "status": "active",
                        "version": "v1",
                    },
                    {
                        "source_name": "missing_source",
                        "source_type": "observation_realtime",
                        "primary_use": "missing source",
                        "trigger_mode": "poll",
                        "write_interval": "1m",
                        "fresh_threshold": "30m",
                        "stale_threshold": "90m",
                        "priority_level": "high",
                        "fallback_policy": "fallback",
                        "status": "active",
                        "version": "v1",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    builder = SourcePolicyStatusBuilder(
        now=datetime(2026, 4, 21, 10, 0, tzinfo=timezone.utc),
        registry_path=registry_path,
        source_inputs={
            "fresh_source": {"path": fresh_path, "timestamp_keys": ("generated_at",)},
            "stale_source": {"path": stale_path, "timestamp_keys": ("generated_at",)},
            "missing_source": {"path": missing_path, "timestamp_keys": ("generated_at",)},
        },
    )

    payload = builder.build()

    assert payload["schema_version"] == "source_policy_status.v1"
    assert payload["overall_status"] == "blocked"
    assert payload["counts"]["fresh"] == 1
    assert payload["counts"]["stale"] == 1
    assert payload["counts"]["unavailable"] == 1
    statuses = {source["source_name"]: source["freshness_status"] for source in payload["sources"]}
    assert statuses["fresh_source"] == "fresh"
    assert statuses["stale_source"] == "stale"
    assert statuses["missing_source"] == "unavailable"
