import json
from pathlib import Path

import typer

from weather_signal_engine.alerts.publisher import AlertPublisher
from weather_signal_engine.ingest.market_loader import MarketLoader
from weather_signal_engine.ingest.rules_loader import RulesLoader
from weather_signal_engine.models.forecast_state import ForecastState
from weather_signal_engine.scoring.signal_scorer import SignalScorer
from weather_signal_engine.storage.repositories import SignalEventRepository
from weather_signal_engine.storage.sqlite import SQLiteStore

app = typer.Typer(help="weather-signal-engine CLI")

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = DATA_DIR / "outputs"

SAMPLE_RULEBOOK = OUTPUT_DIR / "sample_rulebook.json"
SAMPLE_MARKET_SNAPSHOT = OUTPUT_DIR / "sample_market_snapshot.json"
SAMPLE_SIGNAL_JSON = OUTPUT_DIR / "sample_signal_event.json"


@app.command()
def run_once() -> None:
    """Run one signal generation cycle."""
    typer.echo("run_once: not implemented yet")


@app.command()
def emit_sample() -> None:
    """
    Emit one sample signal payload using local sample files.
    """
    if not SAMPLE_RULEBOOK.exists():
        raise FileNotFoundError(f"Missing sample rulebook: {SAMPLE_RULEBOOK}")

    if not SAMPLE_MARKET_SNAPSHOT.exists():
        raise FileNotFoundError(f"Missing sample market snapshot: {SAMPLE_MARKET_SNAPSHOT}")

    # 1. load one rule
    rules_loader = RulesLoader()
    rules = rules_loader.load(SAMPLE_RULEBOOK)
    if not rules:
        raise RuntimeError("No rules found in sample rulebook")

    rule = rules[0]

    # 2. load one market snapshot
    market_loader = MarketLoader()
    market_snapshot = market_loader.load_from_file(SAMPLE_MARKET_SNAPSHOT)

    # 3. construct a minimal forecast state
    # Later this should be created from real forecast extraction output.
    forecast_state = ForecastState(
        location_name=rule.location_name,
        target_date=rule.target_date or "UNKNOWN_DATE",
        variable_name=rule.variable_name,
        latest_forecast_value=28.1,
        source_mode="daily.temperature_2m_max",
        forecast_issued_at="2026-04-11T00:00:00",
        run_to_run_delta=0.2,
        model_band="28",
    )

    # 4. score signal
    scorer = SignalScorer()
    signal = scorer.score(rule, forecast_state, market_snapshot)

    # 5. serialize / publish
    publisher = AlertPublisher()
    payload = publisher.publish(signal)

    # 6. save to sqlite
    store = SQLiteStore()
    repo = SignalEventRepository(store)
    repo.save(signal)

    # 7. export json file
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    SAMPLE_SIGNAL_JSON.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    typer.echo("Sample signal emitted.")
    typer.echo(f"Signal ID: {signal.signal_id}")
    typer.echo(f"Output JSON: {SAMPLE_SIGNAL_JSON}")


if __name__ == "__main__":
    app()
