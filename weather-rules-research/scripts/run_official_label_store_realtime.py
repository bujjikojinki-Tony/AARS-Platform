from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
SCRIPTS = ROOT / "scripts"
for path in (SRC, SCRIPTS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from run_official_label_store import main as run_official_label_store_once
from weather_rules_research.settings import (
    OFFICIAL_HISTORY_JSONL,
    OFFICIAL_LABEL_MAX_CYCLES,
    OFFICIAL_LABEL_REFRESH_INTERVAL_SECONDS,
    OFFICIAL_LABEL_SUMMARY_JSON,
)


def _load_summary() -> dict | None:
    if not OFFICIAL_LABEL_SUMMARY_JSON.exists():
        return None
    return json.loads(OFFICIAL_LABEL_SUMMARY_JSON.read_text(encoding="utf-8"))


def _history_count() -> int:
    if not OFFICIAL_HISTORY_JSONL.exists():
        return 0
    text = OFFICIAL_HISTORY_JSONL.read_text(encoding="utf-8").strip()
    if not text:
        return 0
    return len([line for line in text.splitlines() if line.strip()])


async def main() -> None:
    print("=" * 80)
    print("STARTING OFFICIAL LABEL STORE REALTIME WORKER")
    print(f"Refresh interval : {OFFICIAL_LABEL_REFRESH_INTERVAL_SECONDS}s")
    print(f"Max cycles       : {OFFICIAL_LABEL_MAX_CYCLES or 'infinite'}")
    print(f"History output   : {OFFICIAL_HISTORY_JSONL}")
    print(f"Summary output   : {OFFICIAL_LABEL_SUMMARY_JSON}")
    print("=" * 80)

    cycle = 0
    while True:
        await run_official_label_store_once()
        cycle += 1

        summary = _load_summary() or {}
        print(
            json.dumps(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "cycle": cycle,
                    "history_count": _history_count(),
                    "record_count": summary.get("record_count"),
                    "source_counts": summary.get("source_counts"),
                },
                ensure_ascii=False,
            )
        )

        if OFFICIAL_LABEL_MAX_CYCLES and cycle >= OFFICIAL_LABEL_MAX_CYCLES:
            break

        await asyncio.sleep(OFFICIAL_LABEL_REFRESH_INTERVAL_SECONDS)


if __name__ == "__main__":
    asyncio.run(main())
