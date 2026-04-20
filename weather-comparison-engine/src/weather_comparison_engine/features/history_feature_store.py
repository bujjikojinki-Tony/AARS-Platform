from __future__ import annotations

import glob
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from weather_comparison_engine.probability import ShadowProbabilityEngine
from weather_comparison_engine.schemas.training_sample import TrainingSample


class HistoricalFeatureStoreBuilder:
    def __init__(self) -> None:
        self.shadow_engine = ShadowProbabilityEngine()

    def build_samples(
        self,
        *,
        comparison_rows: list[dict],
        resolver_report: dict | None = None,
        official_records: list[dict] | None = None,
    ) -> list[TrainingSample]:
        resolver_by_market = _resolver_rules_by_market_id(resolver_report)
        official_by_market, official_by_key = _official_maps(official_records or [])

        samples: list[TrainingSample] = []
        for row in comparison_rows:
            market_id = str(row.get("market_id") or "")
            if not market_id:
                continue

            resolver_rule = resolver_by_market.get(market_id)
            probability_state = self.shadow_engine.build_probability_state(
                market_snapshot={
                    "market_id": market_id,
                    "market_probability": row.get("market_probability"),
                    "market_band": row.get("market_band"),
                    "market_family": row.get("market_family"),
                    "market_band_scheme": row.get("market_band_scheme") or row.get("band_scheme"),
                },
                forecast_snapshot={
                    "market_id": market_id,
                    "model_band": row.get("model_band"),
                    "confidence_score": row.get("confidence_score"),
                },
                resolver_rule=resolver_rule,
            )

            official_record = _find_official_record(
                market_id=market_id,
                resolver_rule=resolver_rule,
                official_by_market=official_by_market,
                official_by_key=official_by_key,
            )
            official_value = _to_float((official_record or {}).get("official_value"))
            resolved_band = _classify_official_band(
                official_value=official_value,
                resolver_rule=resolver_rule,
                official_record=official_record,
            )
            expected_band = (
                (resolver_rule or {}).get("expected_band")
                or (official_record or {}).get("expected_band")
                or row.get("market_band")
            )
            outcome = _derive_outcome(target_band=expected_band, resolved_band=resolved_band)

            yes_price = _to_float(row.get("yes_price"))
            no_price = _to_float(row.get("no_price"))
            price_sum = round(yes_price + no_price, 4) if yes_price is not None and no_price is not None else None
            price_dislocation = round(abs((price_sum or 0.0) - 1.0), 4) if price_sum is not None else None

            samples.append(
                TrainingSample(
                    market_id=market_id,
                    timestamp=str(row.get("timestamp") or ""),
                    market_question=(resolver_rule or {}).get("market_question"),
                    market_family=(resolver_rule or {}).get("market_family") or row.get("market_family"),
                    band_scheme=(resolver_rule or {}).get("band_scheme") or row.get("band_scheme"),
                    target_date=(resolver_rule or {}).get("target_date"),
                    variable_name=(resolver_rule or {}).get("variable_name"),
                    station_id=(resolver_rule or {}).get("station_id"),
                    market_probability=_to_float(row.get("market_probability")),
                    yes_price=yes_price,
                    no_price=no_price,
                    price_sum=price_sum,
                    price_dislocation=price_dislocation,
                    model_value=_to_float(row.get("model_value")),
                    model_band=row.get("model_band"),
                    market_band=row.get("market_band"),
                    expected_band=expected_band,
                    confidence_score=_to_float(row.get("confidence_score")),
                    confidence_adjusted_gap=_to_float(row.get("confidence_adjusted_gap")),
                    comparison_status=row.get("comparison_status"),
                    action_hint=row.get("action_hint"),
                    model_probability=probability_state.model_probability,
                    fair_value=probability_state.fair_value,
                    edge=probability_state.edge,
                    confidence_adjusted_edge=probability_state.confidence_adjusted_edge,
                    probability_reason=probability_state.probability_reason,
                    official_value=official_value,
                    resolved_band=resolved_band,
                    outcome=outcome,
                    is_labeled=outcome is not None,
                    label_source=(official_record or {}).get("source"),
                    resolver_status=(resolver_rule or {}).get("resolver_status"),
                    resolver_reason=(resolver_rule or {}).get("resolver_reason"),
                    required_data_source=(resolver_rule or {}).get("required_data_source"),
                )
            )

        samples.sort(key=lambda sample: (sample.timestamp, sample.market_id))
        return samples

    def build_summary(self, samples: list[TrainingSample]) -> dict:
        labeled = [sample for sample in samples if sample.is_labeled]
        unlabeled = [sample for sample in samples if not sample.is_labeled]
        family_counts = Counter(sample.market_family or "unknown" for sample in samples)
        comparison_counts = Counter(sample.comparison_status or "unknown" for sample in samples)
        label_counts = Counter(sample.outcome or "unlabeled" for sample in samples)

        return {
            "schema_version": "feature_store_summary.v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "tracked_rows": len(samples),
            "tracked_markets": len({sample.market_id for sample in samples}),
            "labeled_rows": len(labeled),
            "unlabeled_rows": len(unlabeled),
            "market_family_counts": dict(family_counts),
            "comparison_status_counts": dict(comparison_counts),
            "label_counts": dict(label_counts),
            "avg_abs_edge": _avg([abs(sample.edge) for sample in samples if sample.edge is not None]),
            "avg_abs_confidence_adjusted_edge": _avg(
                [
                    abs(sample.confidence_adjusted_edge)
                    for sample in samples
                    if sample.confidence_adjusted_edge is not None
                ]
            ),
            "note": (
                "Phase 7 feature store is point-in-time from comparison history with optional official-label join. "
                "Official labels remain sparse until settlement-grade history is persisted."
            ),
        }

    def write_samples_jsonl(self, samples: list[TrainingSample], path: str | Path) -> Path:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            json.dumps(sample.model_dump(mode="json", exclude_none=True), ensure_ascii=False)
            for sample in samples
        ]
        out.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        return out

    def write_summary(self, summary: dict, path: str | Path) -> Path:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        return out


def load_comparison_history(path: str | Path) -> list[dict]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    raise ValueError(f"Expected list payload in {path}")


def load_optional_json_records(pattern_or_path: str | Path) -> list[dict]:
    pattern = str(pattern_or_path)
    paths = sorted(glob.glob(pattern)) if any(char in pattern for char in "*?[]") else [pattern]

    records: list[dict] = []
    for raw_path in paths:
        path = Path(raw_path)
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            continue
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            for line in text.splitlines():
                line = line.strip()
                if not line:
                    continue
                item = json.loads(line)
                if isinstance(item, dict):
                    records.append(item)
            continue

        if isinstance(payload, list):
            records.extend(item for item in payload if isinstance(item, dict))
        elif isinstance(payload, dict):
            records.append(payload)

    return records


def _resolver_rules_by_market_id(report: dict | None) -> dict[str, dict]:
    if not report:
        return {}
    rules = report.get("rules") or []
    result: dict[str, dict] = {}
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        market_id = str(rule.get("market_id") or "")
        if market_id:
            result[market_id] = rule
    return result


def _official_maps(records: list[dict]) -> tuple[dict[str, dict], dict[tuple[str, str, str], dict]]:
    by_market: dict[str, dict] = {}
    by_key: dict[tuple[str, str, str], dict] = {}

    for record in records:
        market_id = str(record.get("market_id") or "")
        if market_id:
            by_market[market_id] = record

        station_id = str(record.get("station_id") or "")
        target_date = str(record.get("target_date") or "")
        variable_name = str(record.get("variable_name") or "")
        if station_id and target_date and variable_name:
            by_key[(station_id, target_date, variable_name)] = record

    return by_market, by_key


def _find_official_record(
    *,
    market_id: str,
    resolver_rule: dict | None,
    official_by_market: dict[str, dict],
    official_by_key: dict[tuple[str, str, str], dict],
) -> dict | None:
    if market_id in official_by_market:
        return official_by_market[market_id]

    station_id = str((resolver_rule or {}).get("station_id") or "")
    target_date = str((resolver_rule or {}).get("target_date") or "")
    variable_name = str((resolver_rule or {}).get("variable_name") or "")
    if station_id and target_date and variable_name:
        return official_by_key.get((station_id, target_date, variable_name))

    return None


def _classify_official_band(
    *,
    official_value: float | None,
    resolver_rule: dict | None,
    official_record: dict | None,
) -> str | None:
    if official_record and official_record.get("resolved_band") is not None:
        return str(official_record.get("resolved_band"))

    if official_value is None or not resolver_rule:
        return None

    band_scheme = resolver_rule.get("band_scheme")
    if band_scheme == "temperature_4_bucket":
        return _classify_temperature_band(official_value)
    if band_scheme in {
        "sea_ice_range_3way",
        "precipitation_range_3way",
        "snowfall_range_3way",
        "wind_speed_range_3way",
    }:
        return _classify_range_band(
            official_value,
            lower=_to_float(resolver_rule.get("threshold_lower")),
            upper=_to_float(resolver_rule.get("threshold_upper")),
        )
    if band_scheme == "global_temperature_index_ordinal":
        rank = int(round(official_value))
        return f"top_{rank}"
    return None


def _classify_temperature_band(value: float) -> str:
    rounded = round(value)
    if rounded <= 26:
        return "26_or_below"
    if rounded == 27:
        return "27"
    if rounded == 28:
        return "28"
    return "29_plus"


def _classify_range_band(value: float, *, lower: float | None, upper: float | None) -> str | None:
    if lower is not None and value < lower:
        return "below_range"
    if upper is not None and value > upper:
        return "above_range"
    if lower is not None or upper is not None:
        return "in_range"
    return None


def _derive_outcome(*, target_band: str | None, resolved_band: str | None) -> str | None:
    if not target_band or not resolved_band:
        return None
    return "YES" if target_band == resolved_band else "NO"


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _avg(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 6)
