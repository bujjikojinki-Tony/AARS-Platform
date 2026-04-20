from __future__ import annotations

import json
from pathlib import Path

import typer

from weather_rules_research.pipeline import (
    export_rulebook_bundle,
    export_station_map_bundle,
    run_bias_report_bundle,
)

app = typer.Typer(help="Research-only tooling for Polymarket weather rule analysis.")


@app.command("export-rulebook")
def export_rulebook_command(output_dir: Path = Path("outputs/demo")) -> None:
    """Export a normalized sample rulebook."""
    typer.echo(export_rulebook_bundle(output_dir=output_dir))


@app.command("export-station-map")
def export_station_map_command(output_dir: Path = Path("outputs/demo")) -> None:
    """Export a sample station mapping file."""
    typer.echo(export_station_map_bundle(output_dir=output_dir))


@app.command("run-bias-report")
def run_bias_report_command(output_dir: Path = Path("outputs/demo")) -> None:
    """Export a sample forecast-vs-settlement bias report."""
    result = run_bias_report_bundle(output_dir=output_dir)
    typer.echo(result["report_path"])
    typer.echo(result["summary_path"])
    typer.echo(json.dumps(result["summary"].model_dump(mode="json"), indent=2))


if __name__ == "__main__":
    app()
