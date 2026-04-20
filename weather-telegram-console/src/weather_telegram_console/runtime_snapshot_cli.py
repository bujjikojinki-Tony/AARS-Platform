from __future__ import annotations

import json
from datetime import datetime, timezone

import typer

from weather_telegram_console.integrations.status_api import StatusAPI
from weather_telegram_console.settings import get_telegram_gate_runtime_snapshot_path

app = typer.Typer(help="Export telegram runtime gate snapshot artifact.")


def _resolve_gate_source(status_report: dict) -> str:
    contracts = status_report.get("contracts")
    if isinstance(contracts, dict):
        gate_source = str(contracts.get("gate_source") or "").strip().lower()
        if gate_source in {"api", "unified_fallback", "local_fallback"}:
            return gate_source
        if contracts.get("gate_stack_api_version"):
            return "api"
    if isinstance(status_report.get("gate_stack"), dict):
        return "unified_fallback"
    return "local_fallback"


@app.command()
def export_status_runtime_snapshot() -> None:
    report = StatusAPI().load_latest_status()
    current_market = report.get("current_market") if isinstance(report.get("current_market"), dict) else {}
    contracts = report.get("contracts") if isinstance(report.get("contracts"), dict) else {}
    payload = {
        "schema_version": "telegram_gate_runtime_snapshot.v1",
        "generated_at": str(report.get("generated_at") or datetime.now(timezone.utc).isoformat()),
        "market_id": current_market.get("market_id"),
        "gate_stack": report.get("gate_stack") if isinstance(report.get("gate_stack"), dict) else {},
        "block_reasons": [str(item) for item in report.get("block_reasons") or []],
        "severity": str(report.get("severity") or "medium"),
        "recommended_operator_action": str(
            report.get("recommended_operator_action") or "hold_execution_and_review"
        ),
        "gate_source": _resolve_gate_source(report),
        "source_schema_version": str(
            contracts.get("gate_stack_source_schema_version") or report.get("schema_version") or "unknown"
        ),
    }
    out = get_telegram_gate_runtime_snapshot_path()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
    typer.echo(f"Telegram gate runtime snapshot exported to {out}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
