from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

from weather_rules_research.models.market_rule import MarketRule


def export_rulebook(path: Path, rules: Sequence[MarketRule]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps([rule.model_dump(mode="json") for rule in rules], indent=2),
        encoding="utf-8",
    )
