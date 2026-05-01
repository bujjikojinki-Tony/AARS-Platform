"""Compatibility shim for environments without the optional streamlit-autorefresh package."""

from __future__ import annotations

from typing import Any


def st_autorefresh(*_: Any, **__: Any) -> int:
    """Fallback no-op autorefresh hook.

    The real third-party package triggers periodic reruns. In local or minimal
    environments where the dependency is unavailable, returning 0 keeps the app
    importable and renderable without auto-refresh behavior.
    """

    return 0
