from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from weather_comparison_engine.probability import build_probability_shadow_outputs


def main() -> None:
    outputs = build_probability_shadow_outputs()
    report = outputs["report"]
    report_path = outputs["report_path"]
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"Probability shadow report written to {report_path}")
    print(f"Probability shadow states written to {report.get('state_paths', [])}")


if __name__ == "__main__":
    main()
