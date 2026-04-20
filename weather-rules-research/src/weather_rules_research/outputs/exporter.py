from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from weather_rules_research.models import BiasReportRow, BiasSummary, MarketRule, StationMapEntry


def export_rulebook(output_dir: Path, rules: list[MarketRule]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "rulebook.json"
    path.write_text(
        json.dumps([rule.model_dump(mode="json") for rule in rules], indent=2),
        encoding="utf-8",
    )
    return path


def export_station_map(output_dir: Path, mappings: list[StationMapEntry]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "station_map.json"
    path.write_text(
        json.dumps([mapping.model_dump(mode="json") for mapping in mappings], indent=2),
        encoding="utf-8",
    )
    return path


def export_bias_report(output_dir: Path, rows: list[BiasReportRow]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "forecast_bias_report.csv"
    frame = pd.DataFrame([row.model_dump(mode="json") for row in rows])
    frame.to_csv(path, index=False)
    return path


def export_bias_summary(output_dir: Path, summary: BiasSummary) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "forecast_bias_summary.json"
    path.write_text(json.dumps(summary.model_dump(mode="json"), indent=2), encoding="utf-8")
    return path
