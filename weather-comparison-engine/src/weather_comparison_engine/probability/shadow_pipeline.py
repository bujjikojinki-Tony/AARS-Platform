from __future__ import annotations

import glob
from pathlib import Path

from weather_comparison_engine.ingest.realtime_forecast_loader import RealtimeForecastLoader
from weather_comparison_engine.ingest.realtime_market_loader import RealtimeMarketLoader
from weather_comparison_engine.probability.contract_policy import ProbabilityContractPolicy
from weather_comparison_engine.probability.shadow_probability_engine import ShadowProbabilityEngine
from weather_comparison_engine.probability.shadow_probability_report import (
    build_probability_shadow_report,
    write_probability_shadow_report,
    write_probability_state,
)
from weather_comparison_engine.settings import (
    MODEL_VALIDATION_REPORT_JSON,
    PROBABILITY_SHADOW_REPORT_JSON,
    PROBABILITY_STATES_DIR,
    REALTIME_FORECAST_JSON,
    REALTIME_FORECAST_SNAPSHOTS_GLOB,
    REALTIME_MARKET_JSON,
    REALTIME_MARKET_SNAPSHOTS_GLOB,
    RESOLVER_REPORT_JSON,
)


def build_probability_shadow_outputs() -> dict:
    market_loader = RealtimeMarketLoader()
    forecast_loader = RealtimeForecastLoader()
    engine = ShadowProbabilityEngine()
    validation_report = _load_optional_dict(forecast_loader, MODEL_VALIDATION_REPORT_JSON)
    contract = ProbabilityContractPolicy().evaluate(validation_report)

    market_snapshots = _load_market_snapshots(market_loader)
    if not market_snapshots:
        raise RuntimeError(
            f"No market snapshots found at {REALTIME_MARKET_JSON} or {REALTIME_MARKET_SNAPSHOTS_GLOB}"
        )

    forecast_snapshots = _load_forecast_snapshots(forecast_loader)
    resolver_report = _load_optional_dict(forecast_loader, RESOLVER_REPORT_JSON)

    states = []
    state_paths = []
    for market_snapshot in market_snapshots:
        market_id = str(market_snapshot.get("market_id") or "")
        resolver_rule = _find_resolver_rule(resolver_report, market_id)
        market_forecast = forecast_snapshots.get(market_id)
        state = engine.build_probability_state(
            market_snapshot=market_snapshot,
            forecast_snapshot=market_forecast,
            resolver_rule=resolver_rule,
        ).model_copy(update=contract)
        out = write_probability_state(state, PROBABILITY_STATES_DIR)
        states.append(state)
        state_paths.append(out)

    report = build_probability_shadow_report(states, state_paths, contract=contract)
    report_path = write_probability_shadow_report(report, PROBABILITY_SHADOW_REPORT_JSON)
    return {
        "states": states,
        "state_paths": state_paths,
        "report": report,
        "report_path": report_path,
        "contract": contract,
    }


def _find_resolver_rule(report: dict | None, market_id: str) -> dict | None:
    if not report:
        return None
    rules = report.get("rules") or []
    if not isinstance(rules, list):
        return None
    for rule in rules:
        if isinstance(rule, dict) and str(rule.get("market_id") or "") == str(market_id):
            return rule
    return None


def _load_market_snapshots(loader: RealtimeMarketLoader) -> list[dict]:
    snapshots: list[dict] = []
    seen: set[str] = set()

    candidate_paths = [Path(REALTIME_MARKET_JSON)]
    candidate_paths.extend(Path(path) for path in sorted(glob.glob(REALTIME_MARKET_SNAPSHOTS_GLOB)))

    for path in candidate_paths:
        if not path.exists():
            continue
        try:
            snapshot = loader.load(path)
        except Exception:
            continue
        market_id = str(snapshot.get("market_id") or "")
        if not market_id or market_id in seen:
            continue
        seen.add(market_id)
        snapshots.append(snapshot)

    return snapshots


def _load_forecast_snapshots(loader: RealtimeForecastLoader) -> dict[str, dict]:
    snapshots: dict[str, dict] = {}

    try:
        single = loader.load(REALTIME_FORECAST_JSON)
        market_id = str(single.get("market_id") or "")
        if market_id:
            snapshots[market_id] = single
    except Exception:
        pass

    try:
        many = loader.load_many(REALTIME_FORECAST_SNAPSHOTS_GLOB)
    except Exception:
        many = []

    for snapshot in many:
        market_id = str(snapshot.get("market_id") or "")
        if market_id and market_id not in snapshots:
            snapshots[market_id] = snapshot

    return snapshots


def _load_optional_dict(loader: RealtimeForecastLoader, path: str | Path) -> dict | None:
    src = Path(path)
    if not src.exists():
        return None
    try:
        payload = loader.load(src)
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None
