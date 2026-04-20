import json
from pathlib import Path

import typer

from polymarket_weather_ingest.discovery.weather_filter import WeatherFilter
from polymarket_weather_ingest.ingest.gamma_client import GammaClient
from polymarket_weather_ingest.ingest.market_snapshot_builder import MarketSnapshotBuilder

app = typer.Typer(help="polymarket-weather-ingest CLI")

BASE_DIR = Path(__file__).resolve().parents[2]
OUTPUT_DIR = BASE_DIR / "data" / "outputs"

@app.command()
def fetch_sample_weather() -> None:
    """Fetch one page of active events and export weather-filtered bundles."""
    client = GammaClient()
    events = client.fetch_active_events_sync(limit=20)

    weather_filter = WeatherFilter()
    builder = MarketSnapshotBuilder()

    bundles = []
    for event in events:
        if weather_filter.is_weather_event(event):
            bundles.append(builder.build_from_event(event))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUTPUT_DIR / "sample_weather_bundles.json"
    out.write_text(
        json.dumps([bundle.model_dump() for bundle in bundles], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    typer.echo(f"Exported {len(bundles)} weather bundles to {out}")


if __name__ == "__main__":
    app()
