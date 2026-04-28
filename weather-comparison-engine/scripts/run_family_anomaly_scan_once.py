from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from weather_comparison_engine.monitoring_layer.runners import run_family_anomaly_scan_once


def main() -> None:
    result = run_family_anomaly_scan_once()
    print(json.dumps({k: v for k, v in result.items() if k != "report"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
