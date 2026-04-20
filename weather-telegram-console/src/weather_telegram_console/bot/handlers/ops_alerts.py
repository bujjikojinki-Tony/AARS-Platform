from __future__ import annotations

from typing import Any

try:
    from telegram import Update
    from telegram.ext import ContextTypes
except ModuleNotFoundError:  # pragma: no cover - local offline test fallback
    Update = Any

    class ContextTypes:
        DEFAULT_TYPE = Any

from weather_telegram_console.authz import Authz
from weather_telegram_console.integrations.ops_notification_dispatcher import (
    ack_ops_notification,
    list_pending_ops_notifications,
    mark_ops_notification_sent,
)
from weather_telegram_console.settings import (
    get_admin_allowlist,
    get_ops_dispatch_max_batch,
    get_telegram_ops_delivery_log_path,
    get_telegram_ops_notifications_path,
)


def _is_admin(update: Update) -> bool:
    admin_ids, admin_usernames = get_admin_allowlist()
    authz = Authz(admin_ids, admin_usernames)
    user = getattr(update, "effective_user", None)
    user_id = getattr(user, "id", None)
    username = getattr(user, "username", None)
    return authz.is_admin(user_id, username)


async def opsqueue_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    if not _is_admin(update):
        await update.message.reply_text("Access denied: admin only.")
        return

    raw_max = context.args[0] if context and getattr(context, "args", None) else ""
    try:
        max_batch = int(raw_max) if raw_max else get_ops_dispatch_max_batch()
    except Exception:
        max_batch = get_ops_dispatch_max_batch()
    if max_batch <= 0:
        max_batch = get_ops_dispatch_max_batch()

    queue_path = get_telegram_ops_notifications_path()
    delivery_log_path = get_telegram_ops_delivery_log_path()
    pending = list_pending_ops_notifications(queue_path=queue_path, max_batch=max_batch)
    if not pending:
        await update.message.reply_text("No pending ops notifications.")
        return

    sent_count = 0
    for item in pending:
        text = str(item.get("text") or "")
        if not text:
            continue
        sent_message = await update.message.reply_text(text)
        notification_id = str(item.get("notification_id") or "")
        chat_id = getattr(getattr(update, "effective_chat", None), "id", None)
        message_id = getattr(sent_message, "message_id", None)
        mark_report = mark_ops_notification_sent(
            queue_path=queue_path,
            delivery_log_path=delivery_log_path,
            notification_id=notification_id,
            sent_by="telegram_bot",
            sent_channel="telegram_bot",
            sent_metadata={
                "chat_id": chat_id,
                "message_id": message_id,
            },
        )
        if mark_report.get("sent"):
            sent_count += 1

    await update.message.reply_text(f"Ops queue dispatched: {sent_count} sent.")


async def opsack_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    if not _is_admin(update):
        await update.message.reply_text("Access denied: admin only.")
        return
    if not context or not getattr(context, "args", None):
        await update.message.reply_text("Usage: /opsack <notification_id>")
        return

    notification_id = str(context.args[0] or "").strip()
    user = getattr(update, "effective_user", None)
    acked_by = str(getattr(user, "username", None) or getattr(user, "id", "operator"))
    report = ack_ops_notification(
        queue_path=get_telegram_ops_notifications_path(),
        delivery_log_path=get_telegram_ops_delivery_log_path(),
        notification_id=notification_id,
        acked_by=acked_by,
    )
    if report.get("acked"):
        await update.message.reply_text(f"Acked ops notification: {notification_id}")
        return
    reason = str(report.get("reason") or "unknown")
    await update.message.reply_text(f"Failed to ack {notification_id}: {reason}")
