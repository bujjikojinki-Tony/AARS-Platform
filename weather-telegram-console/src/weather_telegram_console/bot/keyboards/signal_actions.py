try:
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
except ModuleNotFoundError:  # pragma: no cover - local offline test fallback
    class InlineKeyboardButton:  # type: ignore[no-redef]
        def __init__(self, text: str, callback_data: str) -> None:
            self.text = text
            self.callback_data = callback_data

    class InlineKeyboardMarkup:  # type: ignore[no-redef]
        def __init__(self, keyboard: list[list[InlineKeyboardButton]]) -> None:
            self.inline_keyboard = keyboard


def build_signal_actions_keyboard(signal_id: str) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("Watch", callback_data=f"watch:{signal_id}"),
            InlineKeyboardButton("Approve Small", callback_data=f"approve:{signal_id}"),
            InlineKeyboardButton("Ignore", callback_data=f"ignore:{signal_id}"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
