from __future__ import annotations

import argparse
import json
from pathlib import Path

from weather_comparison_engine.advanced_anomaly import write_advanced_anomaly_artifacts
from weather_comparison_engine.settings import (
    ADVANCED_ANOMALY_OUTPUT_DIR,
    COMPARISON_HISTORY_JSON,
    LATEST_DASHBOARD_ROWS_JSON,
    PROBABILITY_STATES_DIR,
    SOURCE_POLICY_STATUS_JSON,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build market_anomaly_event.v2 once.")
    parser.add_argument("--output-dir", type=Path, default=ADVANCED_ANOMALY_OUTPUT_DIR)
    args = parser.parse_args()

    artifacts = write_advanced_anomaly_artifacts(
        output_dir=args.output_dir,
        market_rows=_ensure_list(_load_json(LATEST_DASHBOARD_ROWS_JSON)),
        comparison_history=_ensure_list(_load_json(COMPARISON_HISTORY_JSON)),
        probability_states=_load_probability_states(),
        source_policy_status=_load_json(SOURCE_POLICY_STATUS_JSON),
    )
    print(json.dumps({key: str(value) for key, value in artifacts.items()}, indent=2, ensure_ascii=False))


def _load_json(path: Path) -> list[dict] | dict:
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []


def _ensure_list(payload: list[dict] | dict) -> list[dict]:
    return payload if isinstance(payload, list) else []


def _load_probability_states() -> dict[str, dict]:
    states: dict[str, dict] = {}
    if PROBABILITY_STATES_DIR.exists():
        for path in PROBABILITY_STATES_DIR.glob("*.json"):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if isinstance(payload, dict) and str(payload.get("market_id") or "").strip():
                states[str(payload["market_id"])] = payload
    return states


if __name__ == "__main__":
    main()
