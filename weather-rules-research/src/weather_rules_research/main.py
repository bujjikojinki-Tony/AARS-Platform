from __future__ import annotations

import json
from pathlib import Path

import typer

from weather_rules_research.governance import (
    load_measurement_registry_bundle,
    load_source_policy_registry,
    validate_registry_bundle,
)
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


@app.command("validate-registry")
def validate_registry_command() -> None:
    """Validate source policy and measurement registries."""
    source_registry = load_source_policy_registry()
    measurement_bundle = load_measurement_registry_bundle()
    errors = validate_registry_bundle(
        source_registry=source_registry,
        measurement_bundle=measurement_bundle,
    )
    summary = {
        "ok": not errors,
        "source_policy_sources": len(source_registry.get("sources") or []),
        "measurement_registry_keys": sorted(
            key for key in measurement_bundle.keys() if key.endswith("_registry")
        ),
        "error_count": len(errors),
        "errors": errors,
    }
    typer.echo(json.dumps(summary, indent=2, ensure_ascii=False))
    if errors:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
