from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from weather_telegram_console.integrations.intent_writer import IntentWriter
from weather_telegram_console.integrations.manual_advisory_audit import (
    append_manual_advisory_event,
    build_operator_ack_event,
)
from weather_telegram_console.integrations.signal_api import SignalAPI
from weather_telegram_console.settings import get_manual_advisory_audit_path
from weather_telegram_console.storage.session_repo import ApprovalRepository
from weather_telegram_console.storage.sqlite import SQLiteStore


async def approval_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return

    await query.answer()

    data = query.data or ""
    if ":" not in data:
        await query.edit_message_text("Unknown action.")
        return

    action, signal_id = data.split(":", 1)

    if action == "watch":
        text = f"Signal `{signal_id}` marked as WATCH."
        await query.edit_message_text(text=text, parse_mode="Markdown")
        return

    if action == "ignore":
        text = f"Signal `{signal_id}` marked as IGNORE."
        await query.edit_message_text(text=text, parse_mode="Markdown")
        return

    if action == "approve":
        signal_api = SignalAPI()
        intent_writer = IntentWriter()
        store = SQLiteStore()
        approvals = ApprovalRepository(store)

        operator_user_id = query.from_user.id if query.from_user else 0

        # 1. dedupe: existing active approval
        existing = approvals.find_active_approval(signal_id)
        if existing is not None:
            text = (
                f"Signal `{signal_id}` already has an active approval.\n\n"
                f"Approval ID: `{existing['approval_id']}`\n"
                f"Expires At: `{existing['expires_at']}`\n"
                f"Intent ID: `{existing['intent_id']}`"
            )
            await query.edit_message_text(text=text, parse_mode="Markdown")
            return

        # 2. resolve intent candidate, preferring dashboard-created intent
        signal_payload = signal_api.load_latest_signal()
        market_id = str(signal_payload.get("market_id") or "")
        intent_path = (
            intent_writer.find_pending_by_signal_id(signal_id)
            or (intent_writer.find_pending_by_market_id(market_id) if market_id else None)
            or (intent_writer.find_dashboard_preview_by_market_id(market_id) if market_id else None)
        )

        if intent_path is not None:
            intent_payload = intent_writer.load_payload(intent_path)
            path = intent_path
            intent_source = "existing_dashboard_or_pending_intent"
        else:
            intent_payload = intent_writer.build_small_intent(
                signal_payload=signal_payload,
                side="buy",
                price=0.42,
                size=10.0,
            )
            path = intent_writer.write(intent_payload)
            intent_source = "telegram_generated_intent"

        # 3. create approval record bound to the concrete intent_id
        approval = approvals.create_approval(
            signal_id=signal_id,
            operator_user_id=operator_user_id,
            decision="approve_small",
            ttl_minutes=15,
            intent_id=intent_payload["intent_id"],
        )
        intent_payload["authorization_ref"] = approval["approval_id"]
        intent_payload.setdefault("schema_version", "execution_intent.v1")
        if not str(intent_payload.get("decision_ref") or "").strip():
            intent_payload["decision_ref"] = f"decision_telegram_{signal_id}"
        intent_writer.write(intent_payload)

        if signal_payload.get("execution_mode") == "manual_advisory":
            append_manual_advisory_event(
                get_manual_advisory_audit_path(),
                build_operator_ack_event(
                    signal_payload=signal_payload,
                    approval=approval,
                    operator_user_id=operator_user_id,
                    intent_id=intent_payload["intent_id"],
                ),
            )

        text = (
            f"Signal `{signal_id}` marked as APPROVE SMALL.\n\n"
            f"Approval ID: `{approval['approval_id']}`\n"
            f"Intent ID: `{intent_payload['intent_id']}`\n"
            f"Expires At: `{approval['expires_at']}`\n\n"
            f"Intent Source: `{intent_source}`\n"
            f"Saved to:\n`{path}`"
        )
        await query.edit_message_text(text=text, parse_mode="Markdown")
        return

    await query.edit_message_text(
        text=f"Unknown action for signal `{signal_id}`.",
        parse_mode="Markdown",
    )
