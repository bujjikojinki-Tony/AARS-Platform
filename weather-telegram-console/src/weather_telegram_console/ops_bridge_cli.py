from __future__ import annotations

import json

import typer

from weather_telegram_console.integrations.ops_alert_bridge import (
    sync_ops_alerts_to_notification_queue,
)
from weather_telegram_console.integrations.ops_notification_dispatcher import (
    ack_ops_notification,
    dispatch_ops_notifications,
    summarize_ops_notification_queue,
)
from weather_telegram_console.settings import (
    get_gate_stack_ops_alerts_path,
    get_ops_alert_bridge_max_batch,
    get_ops_dispatch_max_batch,
    get_ops_alert_bridge_state_path,
    get_telegram_ops_delivery_log_path,
    get_telegram_ops_notifications_path,
)

app = typer.Typer(help="Ops alert bridge utilities for Telegram notification queue.")


@app.callback()
def _root() -> None:
    return None


@app.command()
def sync_gate_alerts(
    max_batch: int = typer.Option(
        default=0,
        help="Maximum alerts to enqueue in one sync batch. 0 means use default setting.",
    ),
) -> None:
    effective_max_batch = max_batch if max_batch > 0 else get_ops_alert_bridge_max_batch()
    report = sync_ops_alerts_to_notification_queue(
        alerts_path=get_gate_stack_ops_alerts_path(),
        state_path=get_ops_alert_bridge_state_path(),
        queue_path=get_telegram_ops_notifications_path(),
        max_batch=effective_max_batch,
    )
    typer.echo(json.dumps(report, indent=2, ensure_ascii=False))


@app.command()
def dispatch_ops_queue(
    max_batch: int = typer.Option(
        default=0,
        help="Maximum pending notifications to mark sent. 0 means use default setting.",
    ),
    dry_run: bool = typer.Option(
        default=False,
        help="If true, only preview dispatch IDs without changing queue state.",
    ),
) -> None:
    effective_max_batch = max_batch if max_batch > 0 else get_ops_dispatch_max_batch()
    report = dispatch_ops_notifications(
        queue_path=get_telegram_ops_notifications_path(),
        delivery_log_path=get_telegram_ops_delivery_log_path(),
        max_batch=effective_max_batch,
        dry_run=dry_run,
    )
    typer.echo(json.dumps(report, indent=2, ensure_ascii=False))


@app.command()
def ack_ops(
    notification_id: str = typer.Option(..., help="Notification id to acknowledge."),
    acked_by: str = typer.Option(default="operator", help="Operator/user label."),
) -> None:
    report = ack_ops_notification(
        queue_path=get_telegram_ops_notifications_path(),
        delivery_log_path=get_telegram_ops_delivery_log_path(),
        notification_id=notification_id,
        acked_by=acked_by,
    )
    typer.echo(json.dumps(report, indent=2, ensure_ascii=False))


@app.command("ops-queue-status")
def ops_queue_status() -> None:
    report = summarize_ops_notification_queue(queue_path=get_telegram_ops_notifications_path())
    typer.echo(json.dumps(report, indent=2, ensure_ascii=False))


def main() -> None:
    app()


if __name__ == "__main__":
    main()
