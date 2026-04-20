from __future__ import annotations

import glob
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from weather_rules_research.rules.live_market_resolver import load_rulebook
from weather_rules_research.rules.resolver_report import (
    build_resolved_market_rule,
    build_resolver_report,
    write_resolver_outputs,
)
from weather_rules_research.settings import (
    REALTIME_MARKET_JSON,
    REALTIME_MARKET_SNAPSHOTS_GLOB,
    RESOLVED_MARKET_RULES_DIR,
    RESOLVER_REPORT_JSON,
    RULEBOOK_JSON,
)


def _load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _load_market_snapshots() -> list[dict]:
    snapshots: list[dict] = []
    if REALTIME_MARKET_JSON.exists():
        snapshots.append(_load_json(REALTIME_MARKET_JSON))

    for path in sorted(glob.glob(REALTIME_MARKET_SNAPSHOTS_GLOB)):
        payload = _load_json(path)
        market_id = str(payload.get("market_id") or "")
        if market_id and all(str(item.get("market_id") or "") != market_id for item in snapshots):
            snapshots.append(payload)

    return snapshots


def main() -> None:
    rules = load_rulebook(RULEBOOK_JSON)
    market_snapshots = _load_market_snapshots()
    if not market_snapshots:
        raise RuntimeError(
            f"No market snapshots found at {REALTIME_MARKET_JSON} or {REALTIME_MARKET_SNAPSHOTS_GLOB}"
        )

    resolved_rules = [
        build_resolved_market_rule(snapshot, rules)
        for snapshot in market_snapshots
        if snapshot.get("market_id") is not None
    ]
    write_resolver_outputs(
        resolved_rules=resolved_rules,
        output_dir=RESOLVED_MARKET_RULES_DIR,
        report_path=RESOLVER_REPORT_JSON,
    )

    report = build_resolver_report(resolved_rules)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"Resolver report written to {RESOLVER_REPORT_JSON}")
    print(f"Resolved market rules written to {RESOLVED_MARKET_RULES_DIR}")


if __name__ == "__main__":
    main()

