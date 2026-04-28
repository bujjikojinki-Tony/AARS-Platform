from __future__ import annotations


def build_navigation_keyboard() -> list[list[dict[str, str]]]:
    return [
        [
            {"text": "Status", "callback_data": "nav:status"},
            {"text": "Market", "callback_data": "nav:market"},
            {"text": "Signals", "callback_data": "nav:signals"},
            {"text": "Monitoring", "callback_data": "nav:monitoring"},
        ],
        [
            {"text": "Opportunities", "callback_data": "nav:opportunities"},
        ]
    ]
