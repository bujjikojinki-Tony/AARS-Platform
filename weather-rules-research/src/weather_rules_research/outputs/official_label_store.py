from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from weather_rules_research.models.market_rule import MarketRule
from weather_rules_research.official_obs.station_settlement_backfill import (
    _classify_station_resolved_band,
    _to_float,
    _unit_for_variable,
)
from weather_rules_research.rules.market_taxonomy import classify_market_question
from weather_rules_research.sea_ice import classify_sea_ice_band, extract_sea_ice_extent_value
from weather_rules_research.stations.mapper import StationMapper


class OfficialLabelStoreBuilder:
    def build_records(
        self,
        *,
        resolver_report: dict | None,
        global_temperature_index_snapshot: dict | None,
        sea_ice_extent_snapshot: dict | None,
        station_records: list[dict] | None = None,
    ) -> list[dict]:
        rules = (resolver_report or {}).get("rules") or []
        records: list[dict] = [record for record in (station_records or []) if isinstance(record, dict)]

        for rule in rules:
            if not isinstance(rule, dict):
                continue
            if str(rule.get("resolver_status") or "") != "matched":
                continue

            market_family = str(rule.get("market_family") or "")
            if market_family == "global_temperature_index":
                record = self._build_global_temperature_record(rule, global_temperature_index_snapshot)
                if record is not None:
                    records.append(record)
            elif market_family == "sea_ice_extent":
                record = self._build_sea_ice_record(rule, sea_ice_extent_snapshot)
                if record is not None:
                    records.append(record)

        records.sort(key=lambda record: str(record.get("market_id") or ""))
        return records

    def build_summary(self, records: list[dict]) -> dict:
        family_counts = Counter(str(record.get("market_family") or "unknown") for record in records)
        source_counts = Counter(str(record.get("source") or "unknown") for record in records)

        return {
            "schema_version": "official_label_summary.v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "record_count": len(records),
            "market_family_counts": dict(family_counts),
            "source_counts": dict(source_counts),
            "note": (
                "Snapshot-grade official labels are persisted for market families whose final observable "
                "state can be derived from current external snapshots."
            ),
        }

    def write_records(self, records: list[dict], output_dir: str | Path) -> list[Path]:
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        for path in out_dir.glob("official_record_*.json"):
            path.unlink()

        written: list[Path] = []
        for record in records:
            market_id = str(record.get("market_id") or "")
            if not market_id:
                continue
            out = out_dir / f"official_record_{market_id}.json"
            out.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
            written.append(out)
        return written

    def write_summary(self, summary: dict, path: str | Path) -> Path:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        return out

    def write_history_jsonl(self, records: list[dict], path: str | Path) -> Path:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        lines = [json.dumps(record, ensure_ascii=False) for record in records]
        out.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        return out

    def load_history_jsonl(self, path: str | Path) -> list[dict]:
        src = Path(path)
        if not src.exists():
            return []

        text = src.read_text(encoding="utf-8").strip()
        if not text:
            return []

        records: list[dict] = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            if isinstance(payload, dict):
                records.append(payload)
        return records

    def append_history_jsonl(self, records: list[dict], path: str | Path) -> tuple[Path, int]:
        existing = self.load_history_jsonl(path)
        merged = list(existing)
        seen = {self._history_key(record) for record in existing}
        appended = 0

        for record in records:
            key = self._history_key(record)
            if key in seen:
                continue
            merged.append(record)
            seen.add(key)
            appended += 1

        return self.write_history_jsonl(merged, path), appended

    def _build_global_temperature_record(self, rule: dict, snapshot: dict | None) -> dict | None:
        if not snapshot:
            return None

        ordinal_rank = snapshot.get("ordinal_rank")
        if ordinal_rank is None:
            return None

        return {
            "market_id": rule.get("market_id"),
            "market_question": rule.get("market_question"),
            "market_family": "global_temperature_index",
            "target_date": rule.get("target_date") or snapshot.get("year"),
            "variable_name": "global_temperature_index",
            "official_value": float(ordinal_rank),
            "resolved_band": snapshot.get("band") or f"top_{ordinal_rank}",
            "expected_band": rule.get("expected_band"),
            "source": snapshot.get("source") or "global_temperature_index.snapshot",
            "source_timestamp": snapshot.get("timestamp"),
            "label_type": "snapshot_grade",
            "notes": snapshot.get("notes"),
        }

    def _build_sea_ice_record(self, rule: dict, snapshot: dict | None) -> dict | None:
        if not snapshot:
            return None

        official_value = extract_sea_ice_extent_value(snapshot)
        if official_value is None:
            return None

        lower = _to_float(rule.get("threshold_lower"))
        upper = _to_float(rule.get("threshold_upper"))
        resolved_band = classify_sea_ice_band(official_value, lower=lower, upper=upper)

        return {
            "market_id": rule.get("market_id"),
            "market_question": rule.get("market_question"),
            "market_family": "sea_ice_extent",
            "target_date": rule.get("target_date") or snapshot.get("season_year"),
            "variable_name": "minimum_sea_ice_extent",
            "official_value": float(official_value),
            "resolved_band": resolved_band,
            "expected_band": rule.get("expected_band"),
            "source": snapshot.get("source") or "sea_ice_extent.snapshot",
            "source_timestamp": snapshot.get("timestamp"),
            "unit": snapshot.get("unit") or "million_sq_km",
            "label_type": "snapshot_grade",
            "notes": snapshot.get("notes"),
        }

    @staticmethod
    def _history_key(record: dict) -> tuple[str, str, str, str, str]:
        return (
            str(record.get("market_id") or ""),
            str(record.get("target_date") or ""),
            str(record.get("variable_name") or ""),
            str(record.get("resolved_band") or ""),
            str(record.get("source_timestamp") or record.get("official_value") or ""),
        )

class StationOfficialRecordBuilder:
    def __init__(self, station_mapper: StationMapper | None = None) -> None:
        self.station_mapper = station_mapper

    def build_records(
        self,
        *,
        rules: list[MarketRule],
        scenarios: list[dict],
    ) -> list[dict]:
        rules_by_market = {str(rule.market_id): rule for rule in rules}
        records: list[dict] = []

        for scenario in scenarios:
            market_id = str(scenario.get("market_id") or "")
            rule = rules_by_market.get(market_id)
            if rule is None:
                continue

            station = self.station_mapper.map_rule_to_station(rule) if self.station_mapper is not None else None
            station_id = (
                scenario.get("station_id")
                or (station.nws_station_id if station else None)
                or (station.cdo_station_id if station else None)
                or rule.nws_station_id
                or rule.cdo_station_id
                or rule.station_name
            )
            taxonomy = classify_market_question(rule.market_question)
            official_value = _to_float(scenario.get("official_value"))
            resolved_band = _classify_station_resolved_band(
                band_scheme=taxonomy.band_scheme,
                official_value=official_value,
            )

            records.append(
                {
                    "market_id": market_id,
                    "market_question": rule.market_question,
                    "market_family": taxonomy.market_family,
                    "target_date": str(scenario.get("target_date") or ""),
                    "variable_name": rule.variable_name,
                    "station_id": station_id,
                    "official_value": official_value,
                    "resolved_band": resolved_band,
                    "expected_band": scenario.get("expected_band"),
                    "source": scenario.get("source") or "sample.station_settlement",
                    "source_timestamp": scenario.get("source_timestamp"),
                    "source_url": scenario.get("source_url"),
                    "label_type": scenario.get("label_type") or "settlement_grade",
                    "unit": scenario.get("unit") or _unit_for_variable(rule.variable_name),
                    "notes": scenario.get("notes"),
                }
            )

        return records
