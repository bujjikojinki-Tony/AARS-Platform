from __future__ import annotations


def build_navigation_keyboard() -> list[list[dict[str, str]]]:
    return [
        [
            {"text": "Status", "callback_data": "nav:status"},
            {"text": "Signals", "callback_data": "nav:signals"},
        ]
    ]
